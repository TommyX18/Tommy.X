import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from cart.cart import Cart
from orders.models import Coupon, Order, OrderItem
from payments.models import Payment
from products.models import Category, Product, ProductVariant
from wishlist.models import WishlistItem

from .serializers import (
    AddressSerializer, CartAddSerializer, CartLineSerializer, CartUpdateSerializer,
    CategorySerializer, CreateOrderSerializer, OrderSerializer, PaymentSerializer,
    ProductDetailSerializer, ProductListSerializer, RegisterSerializer, UserSerializer,
    WishlistItemSerializer,
)

User = get_user_model()


# =========================================================
# AUTH
# =========================================================
class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — public registration, returns JWT tokens immediately."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklists the given refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid or missing refresh token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/ — the authenticated user's own profile. Never exposes other users' data."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    """/api/addresses/ — a customer's own saved addresses only."""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# =========================================================
# CATALOG (read-only, public)
# =========================================================
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/categories/ and /api/categories/<slug>/"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    pagination_class = None


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/products/ and /api/products/<id>/ with search, filtering, ordering, pagination."""
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'variants')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'is_featured', 'is_new_arrival', 'brand']
    search_fields = ['name', 'description', 'sku', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class CategoryProductsView(generics.ListAPIView):
    """GET /api/categories/<slug>/products/"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name']

    def get_queryset(self):
        return Product.objects.filter(category__slug=self.kwargs['slug'], is_active=True)

    def get_serializer_context(self):
        return {'request': self.request}


# =========================================================
# CART (session-based — works for guests and authenticated users alike)
# =========================================================
class CartView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = Cart(request)
        totals = cart.totals()
        lines = CartLineSerializer(list(cart), many=True, context={'request': request}).data
        return Response({'items': lines, 'count': len(cart), 'totals': totals})


class CartAddView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = ProductVariant.objects.get(id=serializer.validated_data['variant_id'])
        added = Cart(request).add(variant, serializer.validated_data['quantity'])
        if not added:
            return Response({'detail': 'Not enough stock available.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Added to cart.', 'count': len(Cart(request))}, status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, key):
        serializer = CartUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Cart(request).update(key, serializer.validated_data['quantity'])
        return Response({'detail': 'Cart updated.'})


class CartRemoveView(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, key):
        Cart(request).remove(key)
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================
# WISHLIST (authenticated users only — API mirrors the "must log in" rule)
# =========================================================
class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        deleted, _ = WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
        if not deleted:
            return Response({'detail': 'Not in wishlist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================
# ORDERS (backend always recalculates totals — never trusts client-sent prices)
# =========================================================
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/orders/ and /api/orders/<id>/ — a customer only ever sees their own orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class CreateOrderView(APIView):
    """POST /api/orders/create/ — places an order from the caller's current session cart."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = Cart(request)
        if len(cart) == 0:
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        coupon = None
        code = data.get('coupon_code')
        if code:
            coupon = Coupon.objects.filter(code__iexact=code).first()
            if not coupon:
                return Response({'detail': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        totals = cart.totals(coupon=coupon)
        if totals.get('coupon_error'):
            return Response({'detail': totals['coupon_error']}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for line in cart:
                variant = line['variant']
                variant.refresh_from_db()
                if line['quantity'] > variant.stock_quantity:
                    return Response(
                        {'detail': f"{line['product'].name} ({line['size']}/{line['color']}) no longer has enough stock."},
                        status=status.HTTP_409_CONFLICT,
                    )

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                order_number='TX' + uuid.uuid4().hex[:10].upper(),
                full_name=data['full_name'], phone=data['phone'], email=data.get('email', ''),
                address_line1=data['address_line1'], address_line2=data.get('address_line2', ''),
                city=data['city'], state=data['state'], pincode=data['pincode'],
                coupon=coupon,
                subtotal=totals['subtotal'], discount=totals['discount'],
                shipping=totals['shipping'], gst=totals['gst'], grand_total=totals['grand_total'],
                payment_method='razorpay_demo', is_paid=True, status='confirmed',
            )
            for line in cart:
                variant = line['variant']
                OrderItem.objects.create(
                    order=order, product=line['product'], variant=variant,
                    product_name=line['product'].name, size=line['size'], color=line['color'],
                    price=line['unit_price'], quantity=line['quantity'],
                )
                variant.stock_quantity -= line['quantity']
                variant.save(update_fields=['stock_quantity'])

            if coupon:
                coupon.times_used += 1
                coupon.save(update_fields=['times_used'])

            Payment.objects.create(
                order=order, provider='razorpay',
                provider_order_id=f'order_demo_{order.order_number}',
                provider_payment_id=f'pay_demo_{uuid.uuid4().hex[:12]}',
                amount=order.grand_total, status='paid',
            )

        cart.clear()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(generics.RetrieveAPIView):
    """GET /api/payments/<order_number>/ — payment status for the caller's own order."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order__order_number'
    lookup_url_kwarg = 'order_number'

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)
