from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    full_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    line1 = models.CharField(max_length=200)

    line2 = models.CharField(
        max_length=200,
        blank=True,
    )

    city = models.CharField(max_length=80)

    state = models.CharField(max_length=80)

    pincode = models.CharField(max_length=10)

    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name}, {self.city} - {self.pincode}"