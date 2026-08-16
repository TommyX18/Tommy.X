from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from products import views as product_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),

    # Top-level category pages: /shirts/, /pants/, /tshirts/, /accessories/, /footwear/
    path('shirts/', product_views.category_view, {'slug': 'shirts'}, name='cat_shirts'),
    path('pants/', product_views.category_view, {'slug': 'pants'}, name='cat_pants'),
    path('tshirts/', product_views.category_view, {'slug': 'tshirts'}, name='cat_tshirts'),
    path('accessories/', product_views.category_view, {'slug': 'accessories'}, name='cat_accessories'),
    path('footwear/', product_views.category_view, {'slug': 'footwear'}, name='cat_footwear'),

    path('product/<slug:slug>/', product_views.product_detail, name='product_detail_root'),
    path('search/', product_views.search_view, name='search_root'),

    path('shop/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('orders/', include('orders.urls')),

    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler403 = 'core.views.error_403'
handler500 = 'core.views.error_500'
