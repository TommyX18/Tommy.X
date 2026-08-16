from .cart import Cart


def cart_wishlist(request):
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_count = request.user.wishlist_items.count()
    return {
        'nav_cart_count': len(Cart(request)),
        'nav_wishlist_count': wishlist_count,
    }
