from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import Address
from orders.models import Coupon, Order, OrderItem
from payments.models import Payment
from products.models import Category, Color, Product, ProductImage, ProductVariant, Size
from wishlist.models import WishlistItem

User = get_user_model()


# ---------------- Auth ----------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff')
        read_only_fields = ('id', 'is_staff')


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'full_name', 'phone', 'line1', 'line2', 'city', 'state', 'pincode', 'is_default')


# ---------------- Catalog ----------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'is_active', 'nav_order')


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('id', 'name', 'order')


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ('id', 'name', 'hex_code')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'order')


class ProductVariantSerializer(serializers.ModelSerializer):
    size = SizeSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ('id', 'size', 'color', 'sku', 'stock_quantity', 'price', 'effective_price', 'in_stock')


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'category', 'price', 'original_price',
                   'discount_percentage', 'sku', 'brand', 'is_featured', 'is_new_arrival',
                   'in_stock', 'primary_image')

    def get_primary_image(self, obj):
        img = obj.primary_image
        request = self.context.get('request')
        if img and request:
            return request.build_absolute_uri(img.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'category', 'description', 'short_description',
                   'price', 'original_price', 'discount_percentage', 'sku', 'brand',
                   'is_featured', 'is_new_arrival', 'in_stock', 'images', 'variants',
                   'created_at', 'updated_at')


# ---------------- Cart (session-based; represented for the API as a plain list) ----------------
class CartAddSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_variant_id(self, value):
        if not ProductVariant.objects.filter(id=value).exists():
            raise serializers.ValidationError('Invalid product variant.')
        return value


class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class CartLineSerializer(serializers.Serializer):
    key = serializers.CharField()
    product = ProductListSerializer()
    size = serializers.CharField()
    color = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_stock = serializers.IntegerField()


# ---------------- Wishlist ----------------
class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_id', 'added_at')


# ---------------- Orders ----------------
class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'size', 'color', 'price', 'quantity', 'line_total')


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'order', 'provider', 'provider_order_id', 'provider_payment_id',
                   'amount', 'status', 'created_at')
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'order_number', 'full_name', 'phone', 'email', 'address_line1', 'address_line2',
                   'city', 'state', 'pincode', 'subtotal', 'discount', 'shipping', 'gst', 'grand_total',
                   'payment_method', 'is_paid', 'status', 'created_at', 'items', 'payment')
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    """Creates an order from the caller's current session cart. Backend always recalculates totals."""
    full_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=15)
    email = serializers.EmailField(required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=200)
    address_line2 = serializers.CharField(max_length=200, required=False, allow_blank=True)
    city = serializers.CharField(max_length=80)
    state = serializers.CharField(max_length=80)
    pincode = serializers.CharField(max_length=10)
    coupon_code = serializers.CharField(max_length=30, required=False, allow_blank=True)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ('code', 'description', 'discount_percent', 'discount_amount', 'min_order_value',
                   'valid_from', 'valid_until', 'is_active')
