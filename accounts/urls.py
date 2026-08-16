from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.TommyLoginView.as_view(), name='login'),
    path('logout/', views.TommyLogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('addresses/', views.address_list, name='addresses'),
    path('addresses/add/', views.address_add, name='address_add'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
]
