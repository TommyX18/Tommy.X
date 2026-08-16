from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_detail, name='detail'),
    path('toggle/<int:product_id>/', views.wishlist_toggle, name='toggle'),
    path('move-to-cart/<int:product_id>/', views.wishlist_move_to_cart, name='move_to_cart'),
]
