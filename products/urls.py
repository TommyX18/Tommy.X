from django.urls import path

from . import views


app_name = 'products'


urlpatterns = [

    path(
        'search/',
        views.search_view,
        name='search'
    ),

    path(
        'new-arrivals/',
        views.new_arrivals,
        name='new_arrivals'
    ),

    path(
        'category/<slug:slug>/',
        views.category_view,
        name='category'
    ),

    path(
        'product/<slug:slug>/',
        views.product_detail,
        name='detail'
    ),

    path(
        'buy-now/<slug:slug>/',
        views.buy_now,
        name='buy_now'
    ),

]