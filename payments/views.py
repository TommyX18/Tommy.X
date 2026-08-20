import json

import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order
from .models import Payment
from .services import amount_in_paise, create_provider_order, get_razorpay_client


def _user_can_access_order(request, order):
    if order.user_id:
        return request.user.is_authenticated and order.user_id == request.user.id
    return request.session.get('pending_order_number') == order.order_number


@require_POST
def create_payment(request, order_number):
    """Create a Razorpay order for an already-created TOMMY.X order."""
    order = get_object_or_404(Order, order_number=order_number)

    if not _user_can_access_order(request, order):
        return JsonResponse({'error': 'You are not allowed to pay for this order.'}, status=403)

    if order.is_paid:
        return JsonResponse({'error': 'This order is already paid.'}, status=400)

    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            'provider': 'razorpay',
            'amount': order.grand_total,
            'status': 'pending',
        },
    )

    # Do not create a second provider order if one is already pending.
    if payment.provider_order_id and payment.status in ('pending', 'processing'):
        provider_order_id = payment.provider_order_id
        amount = amount_in_paise(payment.amount)
    else:
        payment.amount = order.grand_total
        payment.status = 'pending'
        payment.provider_payment_id = ''
        payment.provider_signature = ''
        payment.save(update_fields=[
            'amount', 'status', 'provider_payment_id',
            'provider_signature', 'updated_at'
        ])
        provider_order = create_provider_order(payment)
        provider_order_id = provider_order['id']
        amount = provider_order['amount']

    request.session['pending_order_number'] = order.order_number
    request.session.modified = True

    return JsonResponse({
        'key': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': provider_order_id,
        'amount': amount,
        'currency': 'INR',
        'order_number': order.order_number,
        'name': 'TOMMY.X',
        'description': f'TOMMY.X Order {order.order_number}',
        'prefill': {
            'name': order.full_name,
            'email': order.email,
            'contact': order.phone,
        },
    })


@require_POST
def verify_payment(request):
    """Verify Razorpay signature and only then mark the TOMMY.X order paid."""
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({'success': False, 'error': 'Incomplete Razorpay response.'}, status=400)

    payment = get_object_or_404(
        Payment,
        provider_order_id=razorpay_order_id,
    )
    order = payment.order

    if not _user_can_access_order(request, order):
        return JsonResponse({'success': False, 'error': 'You are not allowed to verify this payment.'}, status=403)

    if order.is_paid:
        return JsonResponse({'success': True, 'order_number': order.order_number})

    client = get_razorpay_client()

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })

        # Also verify the payment amount against our server-side order total.
        provider_payment = client.payment.fetch(razorpay_payment_id)
        expected_amount = amount_in_paise(order.grand_total)
        if int(provider_payment.get('amount', 0)) != expected_amount:
            payment.status = 'failed'
            payment.save(update_fields=['status', 'updated_at'])
            return JsonResponse({'success': False, 'error': 'Payment amount mismatch.'}, status=400)

    except razorpay.errors.SignatureVerificationError:
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': False, 'error': 'Payment signature verification failed.'}, status=400)
    except Exception:
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': False, 'error': 'Unable to verify the Razorpay payment.'}, status=400)

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if not order.is_paid:
            # Re-check stock immediately before confirming the paid order.
            for item in order.items.select_related('variant'):
                if item.variant and item.quantity > item.variant.stock_quantity:
                    payment.status = 'failed'
                    payment.save(update_fields=['status', 'updated_at'])
                    return JsonResponse({
                        'success': False,
                        'error': f'Stock is no longer available for {item.product_name}. Please contact TOMMY.X support.'
                    }, status=409)

            for item in order.items.select_related('variant'):
                if item.variant:
                    item.variant.stock_quantity -= item.quantity
                    item.variant.save(update_fields=['stock_quantity'])

            if order.coupon_id:
                from orders.models import Coupon
                Coupon.objects.filter(pk=order.coupon_id).update(times_used=models.F('times_used') + 1)

            order.payment_id = razorpay_payment_id
            order.is_paid = True
            order.status = 'confirmed'
            order.save(update_fields=['payment_id', 'is_paid', 'status'])

            payment.provider_payment_id = razorpay_payment_id
            payment.provider_signature = razorpay_signature
            payment.status = 'paid'
            payment.save(update_fields=[
                'provider_payment_id', 'provider_signature', 'status', 'updated_at'
            ])

    request.session.pop('pending_order_number', None)
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'order_number': order.order_number,
    })


@csrf_exempt
@require_POST
def webhook(request):
    """Razorpay webhook endpoint. Configure this only after deploying publicly."""
    signature = request.headers.get('X-Razorpay-Signature', '')
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    if not webhook_secret:
        return JsonResponse({'error': 'Webhook secret is not configured.'}, status=503)

    client = get_razorpay_client()
    try:
        client.utility.verify_webhook_signature(
            request.body.decode('utf-8'),
            signature,
            webhook_secret,
        )
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid webhook signature.'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        event = payload.get('event', '')
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        provider_payment_id = payment_entity.get('id')
        provider_order_id = payment_entity.get('order_id')

        if event in ('payment.captured', 'order.paid') and provider_order_id:
            payment = Payment.objects.filter(provider_order_id=provider_order_id).select_related('order').first()
            if payment and not payment.order.is_paid:
                # The browser verification remains the primary confirmation path for now.
                # Webhook is intentionally idempotent and records captured payment details.
                payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
                payment.status = 'paid'
                payment.save(update_fields=['provider_payment_id', 'status', 'updated_at'])

    except (ValueError, TypeError, KeyError):
        return JsonResponse({'error': 'Invalid webhook payload.'}, status=400)

    return JsonResponse({'status': 'ok'})
