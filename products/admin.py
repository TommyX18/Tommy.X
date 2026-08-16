from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant, Size, Color


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'nav_order', 'is_active')
    list_editable = ('nav_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'sku', 'category', 'price', 'original_price',
                     'discount_percentage', 'stock_quantity', 'is_active', 'is_featured', 'is_new_arrival')
    list_filter = ('category', 'brand', 'is_active', 'is_featured', 'is_new_arrival')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    list_editable = ('is_active', 'is_featured', 'is_new_arrival')
    readonly_fields = ('created_at', 'updated_at')

    def thumb(self, obj):
        img = obj.primary_image
        if img:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', img.image.url)
        return '-'
    thumb.short_description = 'Image'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'sku', 'stock_quantity', 'effective_price')
    list_filter = ('size', 'color')
    search_fields = ('sku', 'product__name')
