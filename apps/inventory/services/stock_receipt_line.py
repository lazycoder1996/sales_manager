from apps.inventory.models import StockReceiptLine

from rest_framework import serializers


class StockReceiptLineService:

    @staticmethod
    def _validate_product(product):
        if not product.is_active:
            raise serializers.ValidationError({
                "product": "The selected product is inactive."
            })

    @staticmethod
    def _validate_product_variant(
        product,
        product_variant,
    ):
        active_variants = product.variants.filter(
            is_active=True,
        )

        if active_variants.exists():
            if product_variant is None:
                raise serializers.ValidationError({
                    "product_variant": (
                        "A variant is required for this product."
                    )
                })
        else:
            if product_variant is not None:
                raise serializers.ValidationError({
                    "product_variant": (
                        "This product does not have "
                        "an active variant."
                    )
                })

        if product_variant is not None:
            if product_variant.product_id != product.id:
                raise serializers.ValidationError({
                    "product_variant": (
                        "The selected product variant "
                        "does not belong to the selected product."
                    )
                })

            if not product_variant.is_active:
                raise serializers.ValidationError({
                    "product_variant": (
                        "The selected variant is inactive."
                    )
                })

    @staticmethod
    def create(
        stock_receipt,
        product,
        product_variant,
        quantity,
    ):
        StockReceiptLineService._validate_product(product)

        StockReceiptLineService._validate_product_variant(
            product,
            product_variant,
        )

        return StockReceiptLine.objects.create(
            stock_receipt=stock_receipt,
            product=product,
            product_variant=product_variant,
            quantity=quantity,
            unit_cost=product.cost_price,
        )

    @staticmethod
    def update(
        line,
        product=None,
        product_variant=None,
        quantity=None,
        update_product=False,
        update_product_variant=False,
        update_quantity=False,
    ):
        if quantity is not None and quantity < 1:
            raise serializers.ValidationError({
                "quantity": "Quantity must be greater than zero."
            })

        if update_product:
            StockReceiptLineService._validate_product(
                product
            )

        if update_product or update_product_variant:
            final_product = (
                product
                if update_product
                else line.product
            )

            final_product_variant = (
                product_variant
                if update_product_variant
                else line.product_variant
            )

            StockReceiptLineService._validate_product_variant(
                final_product,
                final_product_variant,
            )

        if update_product:
            line.product = product

            # Re-snapshot the cost when the product changes.
            line.unit_cost = product.cost_price

        if update_product_variant:
            line.product_variant = product_variant

        if update_quantity:
            line.quantity = quantity

        update_fields = []

        if update_product:
            update_fields.extend([
                "product",
                "unit_cost",
            ])

        if update_product_variant:
            update_fields.append(
                "product_variant"
            )

        if update_quantity:
            update_fields.append("quantity")

        if update_fields:
            update_fields.append("updated_at")

            line.save(
                update_fields=update_fields,
            )

        return line

    @staticmethod
    def delete(line):
        line.delete()