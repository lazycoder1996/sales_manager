from uuid import UUID

from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import (
    Product,
    ProductVariant,
    SaleLine,
    StockReceiptLine,
)


class StockBalanceService:

    @staticmethod
    def _parse_uuid(value, field_name):
        if value is None:
            return None

        try:
            return UUID(str(value))
        except (ValueError, TypeError, AttributeError):
            raise serializers.ValidationError({
                field_name: "Invalid UUID."
            })

    @staticmethod
    def _get_sold_quantities(
        product_id=None,
        variant_id=None,
    ):
        queryset = SaleLine.objects.filter(
            delivered_quantity__gt=0,
        )

        if product_id is not None:
            queryset = queryset.filter(
                product_id=product_id,
            )

        if variant_id is not None:
            queryset = queryset.filter(
                product_variant_id=variant_id,
            )

        sold_lines = (
            queryset
            .values(
                "product",
                "product_variant",
            )
            .annotate(
                sold=Sum("delivered_quantity"),
            )
        )

        return {
            (
                line["product"],
                line["product_variant"],
            ): line["sold"]
            for line in sold_lines
        }

    @staticmethod
    def get_balance(
        product_id=None,
        variant_id=None,
    ):
        product_id = StockBalanceService._parse_uuid(
            product_id,
            "product",
        )

        variant_id = StockBalanceService._parse_uuid(
            variant_id,
            "variant",
        )

        product = None

        if product_id is not None:
            product = Product.objects.filter(
                id=product_id,
            ).first()

            if product is None:
                raise serializers.ValidationError({
                    "product": "Product not found."
                })

        variant = None

        if variant_id is not None:
            variant = (
                ProductVariant.objects
                .filter(
                    id=variant_id,
                )
                .select_related("product")
                .first()
            )

            if variant is None:
                raise serializers.ValidationError({
                    "variant": "Product variant not found."
                })

            if (
                product is not None
                and variant.product_id != product.id
            ):
                raise serializers.ValidationError({
                    "variant": (
                        "The selected variant does not belong "
                        "to the selected product."
                    )
                })

        queryset = StockReceiptLine.objects.select_related(
            "product",
            "product_variant",
        )

        if product_id is not None:
            queryset = queryset.filter(
                product_id=product_id,
            )

        if variant_id is not None:
            queryset = queryset.filter(
                product_variant_id=variant_id,
            )

        # -----------------------------------
        # SPECIFIC VARIANT
        # -----------------------------------

        if variant is not None:
            line = (
                queryset
                .values(
                    "product",
                    "product__name",
                    "product_variant",
                    "product_variant__size",
                )
                .annotate(
                    received=Sum("quantity"),
                )
                .order_by(
                    "product__name",
                    "product_variant__size",
                )
            )

            line = next(iter(line), None)

            if line is None:
                return []

            received = line["received"]

            sold_quantities = (
                StockBalanceService._get_sold_quantities(
                    product_id=product_id,
                    variant_id=variant_id,
                )
            )

            sold = sold_quantities.get(
                (
                    line["product"],
                    line["product_variant"],
                ),
                0,
            )

            return [{
                "product_id": line["product"],
                "product": line["product__name"],
                "variant_id": line["product_variant"],
                "variant": line["product_variant__size"],
                "received": received,
                "sold": sold,
                "available": received - sold,
            }]

        # -----------------------------------
        # PRODUCT TOTAL
        # -----------------------------------

        if product is not None:
            line = (
                queryset
                .values(
                    "product",
                    "product__name",
                )
                .annotate(
                    received=Sum("quantity"),
                )
                .order_by("product__name")
            )

            line = next(iter(line), None)

            if line is None:
                return []

            received = line["received"]

            sold = (
                SaleLine.objects
                .filter(
                    product_id=product_id,
                    delivered_quantity__gt=0,
                )
                .aggregate(
                    sold=Sum("delivered_quantity"),
                )["sold"]
                or 0
            )

            return [{
                "product_id": line["product"],
                "product": line["product__name"],
                "received": received,
                "sold": sold,
                "available": received - sold,
            }]

        # -----------------------------------
        # ALL STOCK
        # -----------------------------------

        lines = (
            queryset
            .values(
                "product",
                "product__name",
                "product_variant",
                "product_variant__size",
            )
            .annotate(
                received=Sum("quantity"),
            )
            .order_by(
                "product__name",
                "product_variant__size",
            )
        )

        sold_quantities = (
            StockBalanceService._get_sold_quantities()
        )

        balance = []

        for line in lines:
            received = line["received"]

            sold = sold_quantities.get(
                (
                    line["product"],
                    line["product_variant"],
                ),
                0,
            )

            balance.append({
                "product_id": line["product"],
                "product": line["product__name"],
                "variant_id": line["product_variant"],
                "variant": line["product_variant__size"],
                "received": received,
                "sold": sold,
                "available": received - sold,
            })

        return balance