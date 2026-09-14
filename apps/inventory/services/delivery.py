from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import SaleLine, StockReceiptLine


class DeliveryService:

    @staticmethod
    def _validate_sale_paid(sale):
        if not sale.payments.exists():
            raise serializers.ValidationError({
                "sale": (
                    "The sale must be fully paid "
                    "before items can be delivered."
                )
            })

        total = sum(
            (
                line.quantity * line.unit_price
                for line in sale.lines.all()
            ),
            Decimal("0"),
        )

        paid = sum(
            (
                payment.amount
                for payment in sale.payments.all()
            ),
            Decimal("0"),
        )

        if paid != total:
            raise serializers.ValidationError({
                "sale": (
                    "The sale must be fully paid "
                    "before items can be delivered."
                )
            })

    @staticmethod
    def _get_available_stock(
        product_id,
        product_variant_id,
    ):
        received = (
            StockReceiptLine.objects
            .filter(
                product_id=product_id,
                product_variant_id=product_variant_id,
            )
            .aggregate(
                total=Sum("quantity"),
            )["total"]
            or 0
        )

        delivered = (
            SaleLine.objects
            .filter(
                product_id=product_id,
                product_variant_id=product_variant_id,
                delivered_quantity__gt=0,
            )
            .aggregate(
                total=Sum("delivered_quantity"),
            )["total"]
            or 0
        )

        return received - delivered

    @staticmethod
    @transaction.atomic
    def deliver(sale, lines):
        DeliveryService._validate_sale_paid(
            sale
        )

        sale_lines = {
            str(line.id): line
            for line in (
                SaleLine.objects
                .select_for_update()
                .filter(sale=sale)
            )
        }

        # ---------------------------------------------------------
        # First pass:
        # Validate every requested line.
        # Nothing is changed yet.
        # ---------------------------------------------------------

        requested_by_stock_item = {}

        validated_lines = []

        for item in lines:
            line_id = str(item["line_id"])
            quantity = item["quantity"]

            line = sale_lines.get(line_id)

            if line is None:
                raise serializers.ValidationError({
                    "line_id": (
                        "The sale line does not belong "
                        "to this sale."
                    )
                })

            remaining_sale_quantity = (
                line.quantity
                - line.delivered_quantity
            )

            if quantity > remaining_sale_quantity:
                raise serializers.ValidationError({
                    "quantity": (
                        f"Only {remaining_sale_quantity} "
                        f"unit(s) remain to be delivered "
                        f"for this sale line."
                    )
                })

            stock_key = (
                line.product_id,
                line.product_variant_id,
            )

            requested_by_stock_item[stock_key] = (
                requested_by_stock_item.get(
                    stock_key,
                    0,
                )
                + quantity
            )

            validated_lines.append(
                (line, quantity)
            )

        # ---------------------------------------------------------
        # Second pass:
        # Check stock availability for every product/variant.
        # ---------------------------------------------------------

        for (
            product_id,
            product_variant_id,
        ), requested_quantity in (
            requested_by_stock_item.items()
        ):
            available_quantity = (
                DeliveryService._get_available_stock(
                    product_id=product_id,
                    product_variant_id=product_variant_id,
                )
            )

            if requested_quantity > available_quantity:
                raise serializers.ValidationError({
                    "stock": (
                        f"Insufficient stock. "
                        f"Only {available_quantity} "
                        f"unit(s) available for the "
                        f"requested product/variant, "
                        f"but {requested_quantity} "
                        f"unit(s) were requested."
                    )
                })

        # ---------------------------------------------------------
        # Third pass:
        # All validation passed. Now update the delivery.
        # ---------------------------------------------------------

        updated_lines = []

        for line, quantity in validated_lines:
            line.delivered_quantity += quantity

            line.save(
                update_fields=[
                    "delivered_quantity",
                    "updated_at",
                ]
            )

            updated_lines.append(line)

        return updated_lines