from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from orders.models import Coupon
from products.models import ProductVariant
from .cart import Cart


@require_POST
def add_to_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    quantity = int(request.POST.get('quantity', 1))
    if variant.stock_quantity <= 0:
        messages.error(request, f'{variant.product.name} ({variant.size.name}/{variant.color.name}) is out of stock.')
    else:
        added = Cart(request).add(variant, quantity)
        if added:
            messages.success(request, f'{variant.product.name} added to your bag.')
        else:
            messages.error(request, 'Sorry, not enough stock available for that quantity.')
    return redirect(request.POST.get('next') or 'cart:detail')


@require_POST
def update_cart(request, key):
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(key, quantity)
    return redirect('cart:detail')


@require_POST
def remove_from_cart(request, key):
    Cart(request).remove(key)
    return redirect('cart:detail')


def cart_detail(request):
    cart = Cart(request)
    coupon = None
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
    totals = cart.totals(coupon=coupon)
    return render(request, 'cart/detail.html', {'cart': cart, 'totals': totals, 'coupon': coupon})


@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip()
    if code:
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon:
            request.session['coupon_code'] = coupon.code
            messages.success(request, f'Coupon "{coupon.code}" applied.')
        else:
            messages.error(request, 'Invalid coupon code.')
    return redirect('cart:detail')


@require_POST
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart:detail')
