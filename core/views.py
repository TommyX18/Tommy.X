from django.contrib import messages
from django.shortcuts import redirect, render

from products.models import Category, Product

from .models import (
    Offer,
    Story,
    CustomerReview,
    InstagramPost,
)


# ============================================================
# HOME
# ============================================================

def home_view(request):

    context = {
        # ----------------------------------------------------
        # FEATURED PRODUCTS
        # ----------------------------------------------------

        'featured': Product.objects.filter(
            is_featured=True,
            is_active=True
        )[:8],


        # ----------------------------------------------------
        # NEW ARRIVALS
        # ----------------------------------------------------

        'new_arrivals': Product.objects.filter(
            is_new_arrival=True,
            is_active=True
        )[:8],


        # ----------------------------------------------------
        # BEST SELLERS
        # ----------------------------------------------------

        'best_sellers': Product.objects.filter(
            is_active=True
        ).order_by('-created_at')[:8],


        # ----------------------------------------------------
        # SHOP BY CATEGORY
        # ----------------------------------------------------

        'categories': Category.objects.filter(
            is_active=True
        )[:6],


        # ----------------------------------------------------
        # OFFER
        # ----------------------------------------------------

        'offer': Offer.objects.filter(
            is_active=True
        ).first(),


        # ----------------------------------------------------
        # OUR STORY
        # ----------------------------------------------------

        'story': Story.objects.filter(
            is_active=True
        ).first(),


        # ----------------------------------------------------
        # CUSTOMER REVIEWS
        # ----------------------------------------------------

        'reviews': CustomerReview.objects.filter(
            is_active=True
        )[:3],


        # ----------------------------------------------------
        # INSTAGRAM POSTS
        # ----------------------------------------------------

        'instagram_posts': InstagramPost.objects.filter(
            is_active=True
        )[:6],
    }


    return render(
        request,
        'core/home.html',
        context
    )


# ============================================================
# OFFERS
# ============================================================

def offers_view(request):

    products = Product.objects.filter(
        is_active=True,
        original_price__gt=0
    ).exclude(
        price=0
    )


    on_offer = [
        product
        for product in products
        if product.discount_percentage > 0
    ]


    return render(
        request,
        'core/offers.html',
        {
            'products': on_offer
        }
    )


# ============================================================
# CONTACT
# ============================================================

def contact_view(request):

    if request.method == 'POST':

        messages.success(
            request,
            "Thanks for reaching out — we'll get back to you shortly."
        )

        return redirect(
            'core:contact'
        )


    return render(
        request,
        'core/contact.html'
    )


# ============================================================
# ERROR 404
# ============================================================

def error_404(request, exception=None):

    return render(
        request,
        '404.html',
        status=404
    )


# ============================================================
# ERROR 403
# ============================================================

def error_403(request, exception=None):

    return render(
        request,
        '403.html',
        status=403
    )


# ============================================================
# ERROR 500
# ============================================================

def error_500(request):

    return render(
        request,
        '500.html',
        status=500
    )