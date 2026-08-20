from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='api-category')
router.register('products', views.ProductViewSet, basename='api-product')
router.register('orders', views.OrderViewSet, basename='api-order')
router.register('addresses', views.AddressViewSet, basename='api-address')

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='api-login'),          # returns access + refresh
    path('auth/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('auth/me/', views.MeView.as_view(), name='api-me'),

    # Catalog
    path('categories/<slug:slug>/products/', views.CategoryProductsView.as_view(), name='api-category-products'),

    # Cart (session based)
    path('cart/', views.CartView.as_view(), name='api-cart'),
    path('cart/add/', views.CartAddView.as_view(), name='api-cart-add'),
    path('cart/update/<str:key>/', views.CartUpdateView.as_view(), name='api-cart-update'),
    path('cart/remove/<str:key>/', views.CartRemoveView.as_view(), name='api-cart-remove'),

    # Wishlist
    path('wishlist/', views.WishlistView.as_view(), name='api-wishlist'),
    path('wishlist/remove/<int:product_id>/', views.WishlistRemoveView.as_view(), name='api-wishlist-remove'),

    # Orders / Payments
    path('orders/create/', views.CreateOrderView.as_view(), name='api-order-create'),
    path('payments/create/', views.CreatePaymentView.as_view(), name='api-payment-create'),
    path('payments/verify/', views.VerifyPaymentView.as_view(), name='api-payment-verify'),
    path('payments/<str:order_number>/', views.PaymentDetailView.as_view(), name='api-payment-detail'),

    path('', include(router.urls)),
]
