from django.db import models


class Offer(models.Model):
    badge = models.CharField(
        max_length=100,
        default="Limited Time"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    image = models.ImageField(
        upload_to="offers/",
        blank=True,
        null=True
    )

    button_text = models.CharField(
        max_length=100,
        default="Shop Offers"
    )

    button_url = models.CharField(
        max_length=500,
        default="/offers/"
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "display_order",
            "-created_at"
        ]

    def __str__(self):
        return self.title


class Story(models.Model):
    title = models.CharField(
        max_length=200,
        default="Our Story"
    )

    description = models.TextField(
        blank=True
    )

    image = models.ImageField(
        upload_to="stories/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "display_order",
            "-created_at"
        ]

        verbose_name = "Our Story"
        verbose_name_plural = "Our Story"

    def __str__(self):
        return self.title


class CustomerReview(models.Model):
    customer_name = models.CharField(
        max_length=100
    )

    review = models.TextField()

    rating = models.PositiveSmallIntegerField(
        default=5
    )

    is_verified = models.BooleanField(
        default=True
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "display_order",
            "-created_at"
        ]

        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return self.customer_name


class InstagramPost(models.Model):
    image = models.ImageField(
        upload_to="instagram/",
        blank=True,
        null=True
    )

    instagram_url = models.URLField(
        max_length=500,
        help_text=(
            "Paste the Instagram post, reel, "
            "or profile URL."
        )
    )

    caption = models.CharField(
        max_length=200,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "display_order",
            "-created_at"
        ]

        verbose_name = "Instagram Post"
        verbose_name_plural = "Instagram Posts"

    def __str__(self):
        return (
            self.caption
            or f"Instagram Post #{self.pk}"
        )