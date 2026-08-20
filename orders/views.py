import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from payments.models import Payment
from .forms import CheckoutForm
from .models import Coupon, Order, OrderItem


def _get_session_coupon(request):
    code = request.session.get('coupon_code')
    if code:
        return Coupon.objects.filter(code__iexact=code).first()
    return None


def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, 'Your bag is empty.')
        return redirect('cart:detail')

    # Validate stock before creating a pending order.
    for line in cart:
        if line['quantity'] > line['max_stock']:
            messages.error(request, f"Only {line['max_stock']} left for {line['product'].name} ({line['size']}/{line['color']}). Please update your bag.")
            return redirect('cart:detail')

    coupon = _get_session_coupon(request)
    totals = cart.totals(coupon=coupon)
    if totals.get('coupon_error'):
        messages.warning(request, totals['coupon_error'])
        coupon = None

    initial = {}
    if request.user.is_authenticated:
        default_address = request.user.addresses.filter(is_default=True).first() or request.user.addresses.first()
        if default_address:
            initial = {
                'full_name': default_address.full_name,
                'phone': default_address.phone,
                'email': request.user.email,
                'address_line1': default_address.line1,
                'address_line2': default_address.line2,
                'city': default_address.city,
                'state': default_address.state,
                'pincode': default_address.pincode,
            }

    if request.method == 'POST':
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            data = form.cleaned_data

            with transaction.atomic():
                # Re-check stock immediately before creating the order.
                for line in cart:
                    variant = line['variant']
                    variant.refresh_from_db()
                    if line['quantity'] > variant.stock_quantity:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            from django.http import JsonResponse
                            return JsonResponse({'error': f"{line['product'].name} ({line['size']}/{line['color']}) no longer has enough stock."}, status=409)
                        messages.error(request, f"{line['product'].name} ({line['size']}/{line['color']}) no longer has enough stock.")
                        return redirect('cart:detail')

                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    order_number='TX' + uuid.uuid4().hex[:10].upper(),
                    full_name=data['full_name'],
                    phone=data['phone'],
                    email=data['email'],
                    address_line1=data['address_line1'],
                    address_line2=data['address_line2'],
                    city=data['city'],
                    state=data['state'],
                    pincode=data['pincode'],
                    coupon=coupon,
                    subtotal=totals['subtotal'],
                    discount=totals['discount'],
                    shipping=totals['shipping'],
                    gst=totals['gst'],
                    grand_total=totals['grand_total'],
                    payment_method='razorpay',
                    is_paid=False,
                    status='placed',
                )

                for line in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=line['product'],
                        variant=line['variant'],
                        product_name=line['product'].name,
                        size=line['size'],
                        color=line['color'],
                        price=line['unit_price'],
                        quantity=line['quantity'],
                    )

                Payment.objects.create(
                    order=order,
                    provider='razorpay',
                    amount=order.grand_total,
                    status='pending',
                )

            request.session['pending_order_number'] = order.order_number
            request.session.modified = True

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'order_number': order.order_number,
                }, status=201)

            messages.info(request, 'Your order was created. Complete the Razorpay payment to confirm it.')
            return redirect('orders:checkout')
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'totals': totals,
        'coupon': coupon,
    })


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not order.is_paid:
        messages.info(request, 'Payment is not confirmed for this order yet.')
        return redirect('orders:checkout')
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/history.html', {'orders': orders})


def track_order(request):
    order = None
    searched = False
    if request.method == 'POST':
        searched = True
        order_number = request.POST.get('order_number', '').strip()
        phone = request.POST.get('phone', '').strip()
        order = Order.objects.filter(order_number__iexact=order_number, phone=phone).first()
    return render(request, 'orders/track.html', {'order': order, 'searched': searched})


@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status in ('placed', 'confirmed'):
        order.status = 'cancelled'
        order.save()
        for item in order.items.select_related('variant'):
            if item.variant:
                item.variant.stock_quantity += item.quantity
                item.variant.save(update_fields=['stock_quantity'])
        messages.success(request, f'Order {order.order_number} has been cancelled.')
    else:
        messages.error(request, 'This order can no longer be cancelled.')
    return redirect('accounts:profile')
