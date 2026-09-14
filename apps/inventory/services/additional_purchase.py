from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Sale, SaleLine
from apps.inventory.services.payment import PaymentService
from apps.inventory.services.sale_line import (
    SaleLineService,
)


class AdditionalPurchaseService:

    @staticmethod
    @transaction.atomic
    def create(
        sale,
        lines,
        cash_amount,
        momo_amount,
        paid_at,
    ):
        if not lines:
            raise serializers.ValidationError({
                "lines": (
                    "At least one item is required."
                )
            })

        if not Sale.objects.filter(
            id=sale.id
        ).exists():
            raise serializers.ValidationError({
                "sale": "Sale not found."
            })

        created_lines = []

        for line_data in lines:
            product = line_data["product"]
            product_variant = line_data.get(
                "product_variant"
            )
            quantity = line_data["quantity"]

            line = SaleLineService.create(
                sale=sale,
                product=product,
                product_variant=product_variant,
                quantity=quantity,
            )

            created_lines.append(line)

        PaymentService.create(
            sale=sale,
            cash_amount=cash_amount,
            momo_amount=momo_amount,
            paid_at=paid_at,
        )

        return created_lines