from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('offers/', views.offers_view, name='offers'),
    path('contact/', views.contact_view, name='contact'),
]
