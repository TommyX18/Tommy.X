from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'size', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'grand_total', 'status', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid')
    search_fields = ('order_number', 'full_name', 'phone', 'email')
    list_editable = ('status',)
    inlines = [OrderItemInline]
