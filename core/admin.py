from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Offer,
    Story,
    CustomerReview,
    InstagramPost,
)


# ============================================================
# OFFERS
# ============================================================

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):

    list_display = (
        "preview",
        "title",
        "badge",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    list_editable = (
        "is_active",
        "display_order",
    )

    search_fields = (
        "title",
        "description",
        "badge",
    )

    readonly_fields = (
        "preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Offer Content",
            {
                "fields": (
                    "badge",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Offer Image",
            {
                "fields": (
                    "image",
                    "preview",
                )
            },
        ),
        (
            "Button",
            {
                "fields": (
                    "button_text",
                    "button_url",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'style="width:120px;height:80px;'
                'object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )

        return "No Image"


# ============================================================
# OUR STORY
# ============================================================

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):

    list_display = (
        "preview",
        "title",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    list_editable = (
        "is_active",
        "display_order",
    )

    search_fields = (
        "title",
        "description",
    )

    readonly_fields = (
        "preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Story Content",
            {
                "fields": (
                    "title",
                    "description",
                )
            },
        ),
        (
            "Story Image",
            {
                "fields": (
                    "image",
                    "preview",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'style="width:120px;height:80px;'
                'object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )

        return "No Image"


# ============================================================
# CUSTOMER REVIEWS
# ============================================================

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):

    list_display = (
        "customer_name",
        "rating_display",
        "is_verified",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "rating",
        "is_verified",
        "is_active",
    )

    list_editable = (
        "is_verified",
        "is_active",
        "display_order",
    )

    search_fields = (
        "customer_name",
        "review",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer Review",
            {
                "fields": (
                    "customer_name",
                    "review",
                    "rating",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "is_verified",
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(description="Rating")
    def rating_display(self, obj):
        rating = max(0, min(5, obj.rating))

        return (
            "★" * rating
            + "☆" * (5 - rating)
        )


# ============================================================
# INSTAGRAM POSTS
# ============================================================

@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):

    list_display = (
        "preview",
        "caption",
        "instagram_link",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    list_editable = (
        "is_active",
        "display_order",
    )

    search_fields = (
        "caption",
        "instagram_url",
    )

    readonly_fields = (
        "preview_large",
        "instagram_link_large",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Instagram Content",
            {
                "fields": (
                    "image",
                    "preview_large",
                    "instagram_url",
                    "instagram_link_large",
                    "caption",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "is_active",
                    "display_order",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(description="Photo")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'width="65" height="65" '
                'style="object-fit:cover;'
                'border-radius:6px;" />',
                obj.image.url,
            )

        return "No Image"

    @admin.display(description="Instagram")
    def instagram_link(self, obj):
        if obj.instagram_url:
            return format_html(
                '<a href="{}" '
                'target="_blank" '
                'rel="noopener noreferrer">'
                'Open ↗'
                '</a>',
                obj.instagram_url,
            )

        return "No Link"

    @admin.display(description="Image Preview")
    def preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'width="300" '
                'style="max-height:400px;'
                'object-fit:cover;'
                'border-radius:8px;" />',
                obj.image.url,
            )

        return "Upload an image to preview."

    @admin.display(description="Instagram URL")
    def instagram_link_large(self, obj):
        if obj.instagram_url:
            return format_html(
                '<a href="{}" '
                'target="_blank" '
                'rel="noopener noreferrer">'
                '{}'
                '</a>',
                obj.instagram_url,
                obj.instagram_url,
            )

        return "No Instagram URL"