from django.contrib import messages
from django.shortcuts import redirect, render

from products.models import Category, Product


def home_view(request):
    context = {
        'featured': Product.objects.filter(is_featured=True, is_active=True)[:8],
        'new_arrivals': Product.objects.filter(is_new_arrival=True, is_active=True)[:8],
        'best_sellers': Product.objects.filter(is_active=True).order_by('-created_at')[:8],
        'categories': Category.objects.filter(is_active=True)[:6],
    }
    return render(request, 'core/home.html', context)


def offers_view(request):
    products = Product.objects.filter(is_active=True, original_price__gt=0).exclude(price=0)
    on_offer = [p for p in products if p.discount_percentage > 0]
    return render(request, 'core/offers.html', {'products': on_offer})


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Thanks for reaching out — we'll get back to you shortly.")
        return redirect('core:contact')
    return render(request, 'core/contact.html')


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def error_500(request):
    return render(request, '500.html', status=500)
