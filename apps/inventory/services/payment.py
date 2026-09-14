from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Payment


class PaymentService:

    @staticmethod
    def get_sale_total(sale):
        return sum(
            (
                line.quantity * line.unit_price
                for line in sale.lines.all()
            ),
            Decimal("0"),
        )

    @staticmethod
    def get_sale_paid_amount(sale):
        return sum(
            (
                payment.amount
                for payment in sale.payments.all()
            ),
            Decimal("0"),
        )

    @staticmethod
    @transaction.atomic
    def create(
        sale,
        cash_amount,
        momo_amount,
        paid_at,
    ):
        cash_amount = Decimal(cash_amount)
        momo_amount = Decimal(momo_amount)

        payment_amount = (
            cash_amount + momo_amount
        )

        if payment_amount <= 0:
            raise serializers.ValidationError({
                "amount": (
                    "Payment amount must be "
                    "greater than zero."
                )
            })

        sale_total = (
            PaymentService.get_sale_total(sale)
        )

        if sale_total <= 0:
            raise serializers.ValidationError({
                "sale": (
                    "This sale has no items to pay for."
                )
            })

        paid_amount = (
            PaymentService.get_sale_paid_amount(
                sale
            )
        )

        outstanding_amount = (
            sale_total - paid_amount
        )

        if outstanding_amount <= 0:
            raise serializers.ValidationError({
                "sale": (
                    "This sale has already been "
                    "fully paid."
                )
            })

        # Partial payments are not allowed.
        if payment_amount != outstanding_amount:
            raise serializers.ValidationError({
                "amount": (
                    f"Payment must be the full "
                    f"outstanding balance of GHS "
                    f"{outstanding_amount:.2f}."
                )
            })

        return Payment.objects.create(
            sale=sale,
            cash_amount=cash_amount,
            momo_amount=momo_amount,
            amount=payment_amount,
            paid_at=paid_at,
        )