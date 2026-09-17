import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from payments.models import Payment

from .forms import CheckoutForm
from .models import Coupon, Order, OrderItem


# ============================================================
# SESSION COUPON
# ============================================================

def _get_session_coupon(request):
    code = request.session.get('coupon_code')

    if code:
        return Coupon.objects.filter(
            code__iexact=code
        ).first()

    return None


# ============================================================
# BUY NOW CART PREPARATION
# ============================================================

def _prepare_buy_now_cart(request):
    """
    Prepare the session cart for a Buy Now checkout.

    The original cart is saved in a separate session key so
    the customer's existing bag is not permanently lost.
    """

    buy_now = request.session.get('buy_now')

    if not buy_now:
        return False


    variant_id = buy_now.get('variant_id')
    quantity = buy_now.get('quantity', 1)


    if not variant_id:
        request.session.pop('buy_now', None)
        request.session.modified = True
        return False


    try:
        quantity = int(quantity)

    except (TypeError, ValueError):
        quantity = 1


    if quantity < 1:
        quantity = 1


    # --------------------------------------------------------
    # Save the customer's existing cart only once.
    # --------------------------------------------------------

    if 'buy_now_original_cart' not in request.session:

        current_cart = request.session.get(
            'tommyx_cart',
            {}
        )

        request.session['buy_now_original_cart'] = current_cart


    # --------------------------------------------------------
    # Replace active cart with ONLY Buy Now item.
    # --------------------------------------------------------

    request.session['tommyx_cart'] = {
        str(variant_id): {
            'variant_id': int(variant_id),
            'quantity': quantity,
        }
    }

    request.session.modified = True

    return True


# ============================================================
# RESTORE ORIGINAL CART
# ============================================================

def _restore_original_cart(request):
    """
    Restore the customer's normal cart after the Buy Now
    order has been created.
    """

    if 'buy_now_original_cart' in request.session:

        request.session['tommyx_cart'] = request.session.pop(
            'buy_now_original_cart'
        )


    request.session.pop(
        'buy_now',
        None
    )

    request.session.modified = True


# ============================================================
# CHECKOUT CHOICE
# ============================================================

def checkout_choice_view(request):
    """
    Show Guest / Sign In / Sign Up options before checkout.
    """

    buy_now = request.session.get('buy_now')


    # --------------------------------------------------------
    # If Buy Now data is missing, go back to bag.
    # --------------------------------------------------------

    if not buy_now:

        messages.info(
            request,
            'Please select a product before continuing to checkout.'
        )

        return redirect(
            'cart:detail'
        )


    # --------------------------------------------------------
    # Logged-in customer does not need the choice page.
    # --------------------------------------------------------

    if request.user.is_authenticated:

        return redirect(
            'orders:buy_now_continue'
        )


    return render(
        request,
        'orders/checkout_choice.html'
    )


# ============================================================
# BUY NOW CONTINUE
# ============================================================

def buy_now_continue(request):
    """
    Convert the saved Buy Now selection into the active cart
    and continue to the normal checkout page.

    This endpoint is used by both:
    - Continue as Guest
    - Successful Login
    - Successful Registration
    """

    buy_now = request.session.get(
        'buy_now'
    )


    if not buy_now:

        messages.info(
            request,
            'Your Buy Now session has expired. Please select the product again.'
        )

        return redirect(
            'cart:detail'
        )


    # --------------------------------------------------------
    # Prepare temporary Buy Now cart.
    # --------------------------------------------------------

    prepared = _prepare_buy_now_cart(
        request
    )


    if not prepared:

        messages.error(
            request,
            'Unable to prepare your Buy Now order.'
        )

        return redirect(
            'cart:detail'
        )


    # --------------------------------------------------------
    # Continue to existing checkout.
    # --------------------------------------------------------

    return redirect(
        'orders:checkout'
    )


# ============================================================
# NORMAL CHECKOUT
# ============================================================

def checkout_view(request):

    # --------------------------------------------------------
    # If this is a Buy Now session, prepare the cart.
    # --------------------------------------------------------

    if request.session.get('buy_now'):

        _prepare_buy_now_cart(
            request
        )


    # --------------------------------------------------------
    # Create Cart object.
    # --------------------------------------------------------

    cart = Cart(
        request
    )


    # --------------------------------------------------------
    # Empty cart
    # --------------------------------------------------------

    if len(cart) == 0:

        messages.info(
            request,
            'Your bag is empty.'
        )

        return redirect(
            'cart:detail'
        )


    # ========================================================
    # STOCK VALIDATION
    # ========================================================

    for line in cart:

        if line['quantity'] > line['max_stock']:

            messages.error(
                request,
                f"Only {line['max_stock']} left for "
                f"{line['product'].name} "
                f"({line['size']}/{line['color']}). "
                f"Please update your bag."
            )

            return redirect(
                'cart:detail'
            )


    # ========================================================
    # COUPON
    # ========================================================

    coupon = _get_session_coupon(
        request
    )


    totals = cart.totals(
        coupon=coupon
    )


    if totals.get('coupon_error'):

        messages.warning(
            request,
            totals['coupon_error']
        )

        coupon = None


        totals = cart.totals(
            coupon=None
        )


    # ========================================================
    # DEFAULT ADDRESS
    # ========================================================

    initial = {}


    if request.user.is_authenticated:

        default_address = (
            request.user.addresses.filter(
                is_default=True
            ).first()
            or
            request.user.addresses.first()
        )


        if default_address:

            initial = {

                'full_name':
                    default_address.full_name,

                'phone':
                    default_address.phone,

                'email':
                    request.user.email,

                'address_line1':
                    default_address.line1,

                'address_line2':
                    default_address.line2,

                'city':
                    default_address.city,

                'state':
                    default_address.state,

                'pincode':
                    default_address.pincode,
            }


    # ========================================================
    # POST CHECKOUT
    # ========================================================

    if request.method == 'POST':

        form = CheckoutForm(
            request.POST,
            initial=initial
        )


        if form.is_valid():

            data = form.cleaned_data


            # =================================================
            # TRANSACTION
            # =================================================

            with transaction.atomic():

                # ---------------------------------------------
                # Final stock check
                # ---------------------------------------------

                for line in cart:

                    variant = line['variant']

                    variant.refresh_from_db()


                    if line['quantity'] > variant.stock_quantity:

                        if (
                            request.headers.get(
                                'X-Requested-With'
                            )
                            == 'XMLHttpRequest'
                        ):

                            return JsonResponse(
                                {
                                    'error':
                                        f"{line['product'].name} "
                                        f"({line['size']}/{line['color']}) "
                                        f"no longer has enough stock."
                                },
                                status=409
                            )


                        messages.error(
                            request,
                            f"{line['product'].name} "
                            f"({line['size']}/{line['color']}) "
                            f"no longer has enough stock."
                        )


                        return redirect(
                            'cart:detail'
                        )


                # ---------------------------------------------
                # Create order
                # ---------------------------------------------

                order = Order.objects.create(

                    user=(
                        request.user
                        if request.user.is_authenticated
                        else None
                    ),

                    order_number=
                        'TX'
                        + uuid.uuid4().hex[:10].upper(),

                    full_name=
                        data['full_name'],

                    phone=
                        data['phone'],

                    email=
                        data['email'],

                    address_line1=
                        data['address_line1'],

                    address_line2=
                        data['address_line2'],

                    city=
                        data['city'],

                    state=
                        data['state'],

                    pincode=
                        data['pincode'],

                    coupon=
                        coupon,

                    subtotal=
                        totals['subtotal'],

                    discount=
                        totals['discount'],

                    shipping=
                        totals['shipping'],

                    gst=
                        totals['gst'],

                    grand_total=
                        totals['grand_total'],

                    payment_method=
                        'razorpay',

                    is_paid=
                        False,

                    status=
                        'placed',
                )


                # ---------------------------------------------
                # Create order items
                # ---------------------------------------------

                for line in cart:

                    OrderItem.objects.create(

                        order=
                            order,

                        product=
                            line['product'],

                        variant=
                            line['variant'],

                        product_name=
                            line['product'].name,

                        size=
                            line['size'],

                        color=
                            line['color'],

                        price=
                            line['unit_price'],

                        quantity=
                            line['quantity'],
                    )


                # ---------------------------------------------
                # Create payment
                # ---------------------------------------------

                Payment.objects.create(

                    order=
                        order,

                    provider=
                        'razorpay',

                    amount=
                        order.grand_total,

                    status=
                        'pending',
                )


            # =================================================
            # SAVE PENDING ORDER
            # =================================================

            request.session[
                'pending_order_number'
            ] = order.order_number


            request.session.modified = True


            # =================================================
            # BUY NOW CLEANUP
            # =================================================

            if request.session.get(
                'buy_now'
            ):

                _restore_original_cart(
                    request
                )


            # =================================================
            # AJAX RESPONSE
            # =================================================

            if (
                request.headers.get(
                    'X-Requested-With'
                )
                == 'XMLHttpRequest'
            ):

                return JsonResponse(
                    {
                        'success':
                            True,

                        'order_number':
                            order.order_number,
                    },
                    status=201
                )


            # =================================================
            # NORMAL RESPONSE
            # =================================================

            messages.info(
                request,
                'Your order was created. '
                'Complete the Razorpay payment to confirm it.'
            )


            return redirect(
                'orders:checkout'
            )


    else:

        form = CheckoutForm(
            initial=initial
        )


    # ========================================================
    # RENDER CHECKOUT
    # ========================================================

    return render(
        request,
        'orders/checkout.html',
        {
            'form':
                form,

            'cart':
                cart,

            'totals':
                totals,

            'coupon':
                coupon,
        }
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

def order_success(
    request,
    order_number
):

    order = get_object_or_404(
        Order,
        order_number=order_number
    )


    if not order.is_paid:

        messages.info(
            request,
            'Payment is not confirmed for this order yet.'
        )

        return redirect(
            'orders:checkout'
        )


    return render(
        request,
        'orders/success.html',
        {
            'order':
                order
        }
    )


# ============================================================
# ORDER HISTORY
# ============================================================

@login_required
def order_history(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by(
        '-created_at'
    )


    return render(
        request,
        'orders/history.html',
        {
            'orders':
                orders
        }
    )


# ============================================================
# TRACK ORDER
# ============================================================

def track_order(request):

    order = None

    searched = False


    if request.method == 'POST':

        searched = True


        order_number = request.POST.get(
            'order_number',
            ''
        ).strip()


        phone = request.POST.get(
            'phone',
            ''
        ).strip()


        order = Order.objects.filter(
            order_number__iexact=order_number,
            phone=phone
        ).first()


    return render(
        request,
        'orders/track.html',
        {
            'order':
                order,

            'searched':
                searched,
        }
    )


# ============================================================
# CANCEL ORDER
# ============================================================

@login_required
def cancel_order(
    request,
    order_number
):

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )


    if order.status in (
        'placed',
        'confirmed'
    ):

        order.status = 'cancelled'


        order.save()


        for item in order.items.select_related(
            'variant'
        ):

            if item.variant:

                item.variant.stock_quantity += (
                    item.quantity
                )


                item.variant.save(
                    update_fields=[
                        'stock_quantity'
                    ]
                )


        messages.success(
            request,
            f'Order {order.order_number} '
            f'has been cancelled.'
        )


    else:

        messages.error(
            request,
            'This order can no longer be cancelled.'
        )


    return redirect(
        'accounts:profile'
    )