from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/<str:order_number>/', views.order_success, name='success'),
    path('history/', views.order_history, name='history'),
    path('track/', views.track_order, name='track'),
    path('cancel/<str:order_number>/', views.cancel_order, name='cancel'),
]
