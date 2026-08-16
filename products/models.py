from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    nav_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['nav_order', 'name']
        indexes = [models.Index(fields=['slug']), models.Index(fields=['is_active'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        root_slugs = {'shirts': 'cat_shirts', 'pants': 'cat_pants', 'tshirts': 'cat_tshirts',
                       'accessories': 'cat_accessories', 'footwear': 'cat_footwear'}
        if self.slug in root_slugs:
            return reverse(root_slugs[self.slug])
        return reverse('products:category', args=[self.slug])


class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=30, unique=True)
    hex_code = models.CharField(max_length=7, default='#000000', help_text='e.g. #141414')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)

    sku = models.CharField(max_length=40, unique=True, blank=True)
    brand = models.CharField(max_length=60, default='TOMMY.X')
    stock_quantity = models.PositiveIntegerField(default=20)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        if not self.sku:
            self.sku = f'TX{slugify(self.name)[:6].upper()}{Product.objects.count() + 1:04d}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > 0:
            return round((1 - (self.price / self.original_price)) * 100)
        return 0

    # Backward-compatible alias used by some templates
    @property
    def discount_percent(self):
        return self.discount_percentage

    @property
    def mrp(self):
        return self.original_price

    @property
    def total_stock(self):
        agg = self.variants.aggregate(total=models.Sum('stock_quantity'))
        return agg['total'] or 0

    @property
    def in_stock(self):
        if self.variants.exists():
            return self.total_stock > 0
        return self.stock_quantity > 0

    @property
    def primary_image(self):
        return self.images.first()

    @property
    def available_sizes(self):
        return Size.objects.filter(variants__product=self).distinct().order_by('order')

    @property
    def available_colors(self):
        return Color.objects.filter(variants__product=self).distinct()

    @property
    def size_list(self):
        return [s.name for s in self.available_sizes]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=140, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} image {self.order}'


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=10)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                 help_text='Leave blank to use the product price')

    class Meta:
        unique_together = ('product', 'size', 'color')
        indexes = [models.Index(fields=['sku'])]

    def __str__(self):
        return f'{self.product.name} / {self.size.name} / {self.color.name}'

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f'{self.product.sku}-{self.size.name}-{self.color.name[:3].upper()}'
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.price

    @property
    def in_stock(self):
        return self.stock_quantity > 0
