import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product, Size


def _apply_filters(request, qs):
    sizes = request.GET.getlist('size')
    if sizes:
        qs = qs.filter(variants__size__name__in=sizes).distinct()

    stock = request.GET.get('stock')
    if stock == 'in':
        qs = qs.filter(stock_quantity__gt=0)
    elif stock == 'out':
        qs = qs.filter(stock_quantity=0)

    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)

    color = request.GET.get('color')
    if color:
        qs = qs.filter(variants__color__name__iexact=color).distinct()

    sort = request.GET.get('sort', 'recent')
    sort_map = {
        'recent': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name_az': 'name',
        'name_za': '-name',
        'popularity': '-is_featured',
    }
    qs = qs.order_by(sort_map.get(sort, '-created_at'))
    return qs


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    qs = _apply_filters(request, category.products.filter(is_active=True))
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'category': category,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'sort': request.GET.get('sort', 'recent'),
        'selected_sizes': request.GET.getlist('size'),
        'selected_stock': request.GET.get('stock', ''),
        'all_sizes': Size.objects.all(),
    }
    return render(request, 'products/category.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    variants = product.variants.select_related('size', 'color').all()
    variant_json = json.dumps([
        {'id': v.id, 'size': v.size.name, 'color': v.color.name, 'stock': v.stock_quantity}
        for v in variants
    ])
    return render(request, 'products/detail.html', {
        'product': product, 'related': related, 'variant_json': variant_json,
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    results = Product.objects.none()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(category__name__icontains=query) | Q(sku__icontains=query),
            is_active=True,
        ).distinct()
    return render(request, 'products/search.html', {'query': query, 'products': results})


def new_arrivals(request):
    qs = _apply_filters(request, Product.objects.filter(is_new_arrival=True, is_active=True))
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'products/new_arrivals.html', {'page_obj': page_obj, 'products': page_obj.object_list})
