from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('create/<str:order_number>/', views.create_payment, name='create_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('webhook/', views.webhook, name='webhook'),
]
