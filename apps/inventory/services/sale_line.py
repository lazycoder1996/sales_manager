from rest_framework import serializers

from apps.inventory.models import SaleLine


class SaleLineService:

    @staticmethod
    def _validate_product(product):
        if not product.is_active:
            raise serializers.ValidationError({
                "product": (
                    "The selected product is inactive."
                )
            })

    @staticmethod
    def _validate_product_variant(
        product,
        product_variant,
    ):
        active_variants = product.variants.filter(
            is_active=True
        )

        if active_variants.exists():
            if product_variant is None:
                raise serializers.ValidationError({
                    "product_variant": (
                        "A variant is required "
                        "for this product."
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
                        "The selected variant does not "
                        "belong to the selected product."
                    )
                })

            if not product_variant.is_active:
                raise serializers.ValidationError({
                    "product_variant": (
                        "The selected variant is inactive."
                    )
                })

    @staticmethod
    def _validate_duplicate(
        sale,
        product,
        product_variant,
        exclude_line_id=None,
    ):
        queryset = sale.lines.filter(
            product=product,
            product_variant=product_variant,
        )

        if exclude_line_id:
            queryset = queryset.exclude(
                id=exclude_line_id
            )

        if queryset.exists():
            raise serializers.ValidationError({
                "product": (
                    "This product/variant is already "
                    "in this sale."
                )
            })

    @staticmethod
    def create(
        sale,
        product,
        product_variant,
        quantity,
    ):
        SaleLineService._validate_product(
            product
        )

        SaleLineService._validate_product_variant(
            product,
            product_variant,
        )

        # SaleLineService._validate_duplicate(
        #     sale,
        #     product,
        #     product_variant,
        # )

        return SaleLine.objects.create(
            sale=sale,
            product=product,
            product_variant=product_variant,
            quantity=quantity,
            delivered_quantity=0,
            unit_price=product.selling_price,
            unit_cost=product.cost_price,
        )

    @staticmethod
    def update(
        line,
        quantity,
    ):
        if line.sale.payments.exists():
            raise serializers.ValidationError({
                "line": (
                    "An existing sale line cannot be "
                    "changed after a payment has been made."
                )
            })

        if line.delivered_quantity > 0:
            raise serializers.ValidationError({
                "quantity": (
                    "Quantity cannot be changed after "
                    "an item has been delivered."
                )
            })

        if quantity < 1:
            raise serializers.ValidationError({
                "quantity": (
                    "Quantity must be at least 1."
                )
            })

        line.quantity = quantity

        line.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        return line

    @staticmethod
    def delete(line):
        if line.sale.payments.exists():
            raise serializers.ValidationError({
                "line": (
                    "An existing sale line cannot be "
                    "deleted after a payment has been made."
                )
            })

        if line.delivered_quantity > 0:
            raise serializers.ValidationError({
                "line": (
                    "A sale line cannot be deleted after "
                    "an item has been delivered."
                )
            })

        line.delete()