from decimal import Decimal

from products.models import ProductVariant

CART_SESSION_KEY = 'tommyx_cart'

GST_RATE = Decimal('0.05')
FREE_SHIPPING_THRESHOLD = Decimal('1499')
SHIPPING_CHARGE = Decimal('99')


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, variant, quantity=1):
        """Add a ProductVariant to the cart, respecting available stock."""
        key = str(variant.id)
        current_qty = self.cart.get(key, {}).get('quantity', 0)
        new_qty = min(current_qty + quantity, variant.stock_quantity)
        if new_qty <= 0:
            return False
        self.cart[key] = {'variant_id': variant.id, 'quantity': new_qty}
        self.save()
        return True

    def update(self, key, quantity):
        if key in self.cart:
            variant = ProductVariant.objects.filter(id=self.cart[key]['variant_id']).first()
            if quantity <= 0:
                del self.cart[key]
            else:
                capped = min(quantity, variant.stock_quantity) if variant else quantity
                self.cart[key]['quantity'] = capped
            self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        variant_ids = [item['variant_id'] for item in self.cart.values()]
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product', 'size', 'color').prefetch_related('product__images')
        variants_map = {v.id: v for v in variants}
        for key, item in self.cart.items():
            variant = variants_map.get(item['variant_id'])
            if not variant:
                continue
            line_total = variant.effective_price * item['quantity']
            yield {
                'key': key,
                'variant': variant,
                'product': variant.product,
                'size': variant.size.name,
                'color': variant.color.name,
                'quantity': item['quantity'],
                'unit_price': variant.effective_price,
                'line_total': line_total,
                'max_stock': variant.stock_quantity,
            }

    def totals(self, coupon=None):
        subtotal = Decimal('0')
        for line in self:
            subtotal += line['line_total']

        discount = Decimal('0')
        coupon_error = None
        if coupon:
            valid, msg = coupon.is_valid(subtotal)
            if valid:
                discount = coupon.calculate_discount(subtotal)
            else:
                coupon_error = msg

        discounted = max(subtotal - discount, Decimal('0'))
        shipping = Decimal('0') if discounted >= FREE_SHIPPING_THRESHOLD or discounted == 0 else SHIPPING_CHARGE
        gst = (discounted * GST_RATE).quantize(Decimal('0.01'))
        grand_total = (discounted + shipping + gst).quantize(Decimal('0.01'))
        return {
            'subtotal': subtotal,
            'discount': discount,
            'coupon_error': coupon_error,
            'shipping': shipping,
            'gst': gst,
            'grand_total': grand_total,
        }
