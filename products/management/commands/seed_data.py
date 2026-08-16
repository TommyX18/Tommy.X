import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from orders.models import Coupon
from products.models import Category, Color, Product, ProductImage, ProductVariant, Size

PANEL = (244, 242, 238)
INK = (20, 20, 20)
ORANGE = (232, 93, 31)

CATEGORY_SEED = [
    # (name shown in nav, slug used in URL, nav_order)
    ('Shirts', 'shirts', 0),
    ('Pants', 'pants', 1),
    ('TShirts', 'tshirts', 2),
    ('Accessories', 'accessories', 3),
    ('Footwear', 'footwear', 4),
]

SIZE_SEED = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
COLOR_SEED = [
    ('Black', '#141414'), ('Navy', '#1c2b45'), ('Brown', '#6b4a2f'),
    ('Cream', '#efe6d8'), ('Grey', '#8a8a8a'), ('Red', '#b5342a'), ('White', '#f5f5f5'),
]

PRODUCTS_SEED = {
    'shirts': [
        ('Crimson Clay Check Shirt', 'Red', 949, 1499),
        ('Navy Crest Check Shirt', 'Navy', 949, 1499),
        ('Cocoa Beige Check Shirt', 'Brown', 949, 1499),
        ('Graphite Silver Check Shirt', 'Grey', 949, 1499),
        ('Onyx Black Oxford Shirt', 'Black', 1099, 1699),
        ('Cream Linen Shirt', 'Cream', 1199, 1799),
    ],
    'pants': [
        ('Onyx Black Straight Fit Jeans', 'Black', 999, 1499),
        ('Shadow Fade Straight Fit Jeans', 'Navy', 999, 1499),
        ('Frostlight Straight Fit Jeans', 'Grey', 999, 1499),
        ('Noir Ease Straight-Fit Linen Pants', 'Black', 999, 1499),
        ('Cargo Utility Pants', 'Brown', 1099, 1599),
    ],
    'tshirts': [
        ('Brown Waffle Henley Tee', 'Brown', 899, 1399),
        ('Cream Waffle Henley Tee', 'Cream', 899, 1399),
        ('Noir Waffle Henley Tee', 'Black', 899, 1399),
        ('Choco Stitch Varsity Tee', 'Brown', 899, 1399),
        ('White Essential Crew Tee', 'White', 699, 999),
    ],
    'accessories': [
        ('Leather Bifold Wallet', 'Black', 799, 1199),
        ('Canvas Structured Cap', 'Black', 599, 899),
        ('Woven Leather Belt', 'Brown', 699, 999),
    ],
    'footwear': [
        ('Chelsea Leather Boot', 'Black', 2499, 3499),
        ('Low-Top Court Sneaker', 'White', 1999, 2999),
        ('Suede Desert Boot', 'Brown', 2299, 3199),
    ],
}

COUPON_SEED = [
    ('WELCOME10', 'Flat 10% off on your first order', 10, 0, 999),
    ('FREESHIP', 'Free shipping on orders above Rs.999', 0, 99, 999),
    ('FLAT200', 'Flat Rs.200 off on orders above Rs.1999', 0, 200, 1999),
]


def make_placeholder_image(text, size=(700, 900)):
    img = Image.new('RGB', size, PANEL)
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, 110
    draw.line([(cx, cy - 40), (cx, cy)], fill=INK, width=4)
    draw.arc([cx - 8, cy - 48, cx + 8, cy - 32], 0, 360, fill=INK, width=4)
    draw.line([(cx - 160, cy + 40), (cx, cy), (cx + 160, cy + 40)], fill=INK, width=4, joint='curve')
    draw.rounded_rectangle(
        [size[0] * 0.22, cy + 40, size[0] * 0.78, size[1] - 120],
        radius=18, outline=INK, width=3
    )
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    label = text if len(text) < 26 else text[:23] + '...'
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0] - tw) / 2, size[1] - 70), label, fill=INK, font=font)
    draw.rectangle([0, size[1] - 14, size[0], size[1]], fill=ORANGE)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return ContentFile(buffer.getvalue(), name=f'{text[:40]}.jpg')


class Command(BaseCommand):
    help = 'Seed TOMMY.X with categories, sizes, colors, products, variants and coupons.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing catalog data first.')

    def handle(self, *args, **options):
        if options['flush']:
            ProductVariant.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing catalog.'))

        # Categories
        cat_objs = {}
        for name, slug, order in CATEGORY_SEED:
            cat, _ = Category.objects.update_or_create(slug=slug, defaults={'name': name, 'nav_order': order, 'is_active': True})
            cat_objs[slug] = cat
        self.stdout.write(self.style.SUCCESS(f'Categories ready: {", ".join(c.name for c in cat_objs.values())}'))

        # Sizes
        size_objs = {}
        for i, name in enumerate(SIZE_SEED):
            size_objs[name], _ = Size.objects.get_or_create(name=name, defaults={'order': i})

        # Colors
        color_objs = {}
        for name, hex_code in COLOR_SEED:
            color_objs[name], _ = Color.objects.get_or_create(name=name, defaults={'hex_code': hex_code})

        # Products + variants
        created = 0
        for cat_slug, items in PRODUCTS_SEED.items():
            category = cat_objs[cat_slug]
            for name, color_name, price, original_price in items:
                if Product.objects.filter(name=name).exists():
                    continue
                product = Product.objects.create(
                    category=category,
                    name=name,
                    short_description=f'{name} from the TOMMY.X {category.name.lower()} collection.',
                    description=f'{name} — part of the TOMMY.X {category.name.lower()} collection. Clean lines, honest fabric, made for everyday wear.',
                    price=price,
                    original_price=original_price,
                    brand='TOMMY.X',
                    stock_quantity=0,  # stock now tracked per-variant
                    is_new_arrival=random.random() < 0.4,
                    is_featured=random.random() < 0.35,
                )
                img_file = make_placeholder_image(name)
                ProductImage.objects.create(product=product, image=img_file, alt_text=name, order=0)

                sizes_for_product = SIZE_SEED[1:5] if cat_slug != 'accessories' else ['M', 'L']
                colors_for_product = [color_name, 'Black'] if color_name != 'Black' else ['Black', 'Grey']
                for size_name in sizes_for_product:
                    for cname in dict.fromkeys(colors_for_product):  # de-dupe, preserve order
                        ProductVariant.objects.create(
                            product=product,
                            size=size_objs[size_name],
                            color=color_objs[cname],
                            stock_quantity=random.randint(0, 25),
                        )
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seed complete — {created} products created with size/color variants.'))

        # Coupons
        for code, desc, pct, amt, min_val in COUPON_SEED:
            Coupon.objects.get_or_create(
                code=code,
                defaults={
                    'description': desc,
                    'discount_percent': pct,
                    'discount_amount': amt,
                    'min_order_value': min_val,
                    'valid_from': timezone.now(),
                    'is_active': True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'Coupons ready: {", ".join(c for c, *_ in COUPON_SEED)}'))
