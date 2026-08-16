from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product, ProductVariant

STATUS_CHOICES = [
    ('placed', 'Placed'),
    ('confirmed', 'Confirmed'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_percent = models.PositiveIntegerField(default=0, help_text='0-100. Leave 0 if using a flat amount instead.')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Flat Rs. discount. Leave 0 if using a percentage instead.')
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    times_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self, order_value):
        if not self.is_active:
            return False, 'This coupon is no longer active.'
        now = timezone.now()
        if now < self.valid_from:
            return False, 'This coupon is not active yet.'
        if self.valid_until and now > self.valid_until:
            return False, 'This coupon has expired.'
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, 'This coupon has reached its usage limit.'
        if order_value < self.min_order_value:
            return False, f'Minimum order value for this coupon is Rs.{self.min_order_value}.'
        return True, ''

    def calculate_discount(self, order_value):
        if self.discount_percent:
            return (order_value * Decimal(self.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
        return min(self.discount_amount, order_value)


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=10)

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, default='razorpay')
    payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['order_number']), models.Index(fields=['status'])]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=140)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=30, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'

