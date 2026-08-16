from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.cart import Cart
from products.models import Product, ProductVariant
from .models import WishlistItem


@login_required
def wishlist_detail(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__images')
    return render(request, 'wishlist/detail.html', {'items': items})


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, 'Removed from wishlist.')
    else:
        messages.success(request, 'Added to wishlist.')
    return redirect(request.POST.get('next') or 'wishlist:detail')


@login_required
@require_POST
def wishlist_move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant = product.variants.filter(stock_quantity__gt=0).first()
    if variant:
        Cart(request).add(variant, quantity=1)
        WishlistItem.objects.filter(user=request.user, product=product).delete()
        messages.success(request, f'{product.name} moved to your bag.')
    else:
        messages.error(request, f'{product.name} has no stock available right now.')
    return redirect('wishlist:detail')
