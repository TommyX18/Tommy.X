from decimal import Decimal

import razorpay

from django.conf import settings

from .models import Payment


def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError(
            "Razorpay keys are not configured. "
            "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env."
        )

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


def amount_in_paise(amount: Decimal) -> int:
    return int(
        (amount * Decimal("100")).quantize(Decimal("1"))
    )


def create_provider_order(payment: Payment):
    client = get_razorpay_client()

    amount = amount_in_paise(payment.amount)

    provider_order = client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": payment.order.order_number,
            "notes": {
                "tommyx_order_number": payment.order.order_number,
            },
        }
    )

    payment.provider_order_id = provider_order["id"]
    payment.status = "processing"

    payment.save(
        update_fields=[
            "provider_order_id",
            "status",
            "updated_at",
        ]
    )

    return provider_order