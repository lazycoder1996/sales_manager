from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import Product
from apps.inventory.models import ProductVariant
from apps.inventory.models import SaleLine
from apps.inventory.models import StockReceiptLine


class StockReceiptLineService:

    @staticmethod
    def _validate_product(product):
        if not product.is_active:
            raise serializers.ValidationError(
                "Product is inactive."
            )

    @staticmethod
    def _validate_product_variant(
        product,
        product_variant,
    ):
        active_variants = product.variants.filter(
            is_active=True,
        )

        if (
            active_variants.exists()
            and product_variant is None
        ):
            raise serializers.ValidationError(
                "A variant is required for this product."
            )

        if (
            not active_variants.exists()
            and product_variant is not None
        ):
            raise serializers.ValidationError(
                "This product does not have variants."
            )

        if product_variant is not None:
            if product_variant.product_id != product.id:
                raise serializers.ValidationError(
                    "The selected variant does not belong to "
                    "the selected product."
                )

            if not product_variant.is_active:
                raise serializers.ValidationError(
                    "Product variant is inactive."
                )

    @staticmethod
    def _get_received_quantity(
        product_id,
        product_variant_id,
        exclude_line_id=None,
    ):
        """
        Return the total physical quantity received for a
        product + variant.

        Optionally excludes one receipt line. This is used when
        validating edits or deletion of an existing receipt line.
        """

        queryset = StockReceiptLine.objects.filter(
            product_id=product_id,
            product_variant_id=product_variant_id,
        )

        if exclude_line_id is not None:
            queryset = queryset.exclude(
                id=exclude_line_id,
            )

        return (
            queryset.aggregate(
                total=Sum("quantity"),
            )["total"]
            or 0
        )

    @staticmethod
    def _get_delivered_quantity(
        product_id,
        product_variant_id,
    ):
        """
        Return the total quantity physically delivered for a
        product + variant across all sales.
        """

        return (
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

    @staticmethod
    def _validate_physical_stock_after_change(
        *,
        product_id,
        product_variant_id,
        new_quantity,
        exclude_line_id=None,
    ):
        """
        Validate that changing a receipt line will not make
        physical stock negative.

        Physical stock is:

            total received - total delivered

        The resulting received quantity must therefore never
        be less than the quantity already delivered.
        """

        received_without_line = (
            StockReceiptLineService
            ._get_received_quantity(
                product_id=product_id,
                product_variant_id=product_variant_id,
                exclude_line_id=exclude_line_id,
            )
        )

        resulting_received = (
            received_without_line
            + new_quantity
        )

        delivered = (
            StockReceiptLineService
            ._get_delivered_quantity(
                product_id=product_id,
                product_variant_id=product_variant_id,
            )
        )

        if resulting_received < delivered:
            available_after_change = (
                resulting_received - delivered
            )

            raise serializers.ValidationError(
                {
                    "quantity": (
                        "This change would make physical stock "
                        f"negative. After the change, "
                        f"received stock would be "
                        f"{resulting_received} unit(s), while "
                        f"{delivered} unit(s) have already been "
                        f"delivered. "
                        f"Available stock would be "
                        f"{available_after_change} unit(s)."
                    )
                }
            )

    @staticmethod
    @transaction.atomic
    def create(
        stock_receipt,
        product,
        product_variant,
        quantity,
    ):
        StockReceiptLineService._validate_product(
            product,
        )

        StockReceiptLineService._validate_product_variant(
            product,
            product_variant,
        )

        if quantity < 1:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        line = StockReceiptLine.objects.create(
            stock_receipt=stock_receipt,
            product=product,
            product_variant=product_variant,
            quantity=quantity,
            unit_cost=product.cost_price,
        )

        return line

    @staticmethod
    @transaction.atomic
    def update(
        line,
        product=None,
        product_variant=None,
        quantity=None,
        update_product=False,
        update_product_variant=False,
        update_quantity=False,
    ):
        locked_line = (
            StockReceiptLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        current_product = locked_line.product
        current_variant = locked_line.product_variant
        current_quantity = locked_line.quantity

        final_product = (
            product
            if update_product
            else current_product
        )

        final_variant = (
            product_variant
            if update_product_variant
            else current_variant
        )

        final_quantity = (
            quantity
            if update_quantity
            else current_quantity
        )

        # ---------------------------------------------------------
        # Validate product.
        # ---------------------------------------------------------

        if update_product:
            StockReceiptLineService._validate_product(
                final_product,
            )

        # ---------------------------------------------------------
        # Validate product variant.
        # ---------------------------------------------------------

        if (
            update_product
            or update_product_variant
        ):
            StockReceiptLineService._validate_product_variant(
                final_product,
                final_variant,
            )

        # ---------------------------------------------------------
        # Validate quantity.
        # ---------------------------------------------------------

        if update_quantity:
            if quantity is None or quantity < 1:
                raise serializers.ValidationError(
                    "Quantity must be greater than zero."
                )

        # ---------------------------------------------------------
        # Physical stock validation.
        #
        # If the product/variant changes, the old stock key loses
        # this receipt line and the new stock key gains it.
        #
        # If only quantity changes, the same stock key is checked
        # with the new quantity.
        # ---------------------------------------------------------

        current_stock_key = (
            current_product.id,
            current_variant.id
            if current_variant is not None
            else None,
        )

        final_stock_key = (
            final_product.id,
            final_variant.id
            if final_variant is not None
            else None,
        )

        stock_key_changed = (
            current_stock_key
            != final_stock_key
        )

        if stock_key_changed:
            # Removing this receipt line from the old product/variant
            # must not make already-delivered stock exceed the
            # remaining received stock.
            delivered_from_old_key = (
                StockReceiptLineService
                ._get_delivered_quantity(
                    product_id=current_product.id,
                    product_variant_id=(
                        current_variant.id
                        if current_variant is not None
                        else None
                    ),
                )
            )

            remaining_old_received = (
                StockReceiptLineService
                ._get_received_quantity(
                    product_id=current_product.id,
                    product_variant_id=(
                        current_variant.id
                        if current_variant is not None
                        else None
                    ),
                    exclude_line_id=locked_line.id,
                )
            )

            if remaining_old_received < delivered_from_old_key:
                raise serializers.ValidationError(
                    {
                        "product": (
                            "The product or variant cannot be changed "
                            "because removing this receipt line would "
                            "make physical stock negative."
                        )
                    }
                )

        # Check the final stock key when the line is being moved
        # or its quantity is being changed.
        StockReceiptLineService._validate_physical_stock_after_change(
            product_id=final_product.id,
            product_variant_id=(
                final_variant.id
                if final_variant is not None
                else None
            ),
            new_quantity=final_quantity,
            exclude_line_id=(
                locked_line.id
                if not stock_key_changed
                else None
            ),
        )

        # ---------------------------------------------------------
        # Apply changes.
        # ---------------------------------------------------------

        if update_product:
            locked_line.product = final_product
            locked_line.unit_cost = final_product.cost_price

        if update_product_variant:
            locked_line.product_variant = final_variant

        if update_quantity:
            locked_line.quantity = final_quantity

        locked_line.save(
            update_fields=[
                "product",
                "product_variant",
                "quantity",
                "unit_cost",
                "updated_at",
            ],
        )

        return locked_line

    @staticmethod
    @transaction.atomic
    def delete(line):
        locked_line = (
            StockReceiptLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        delivered = (
            StockReceiptLineService
            ._get_delivered_quantity(
                product_id=locked_line.product_id,
                product_variant_id=locked_line.product_variant_id,
            )
        )

        remaining_received = (
            StockReceiptLineService
            ._get_received_quantity(
                product_id=locked_line.product_id,
                product_variant_id=locked_line.product_variant_id,
                exclude_line_id=locked_line.id,
            )
        )

        if remaining_received < delivered:
            raise serializers.ValidationError(
                {
                    "line": (
                        "This receipt line cannot be deleted because "
                        "removing it would make physical stock negative. "
                        f"{delivered} unit(s) have already been delivered, "
                        f"but only {remaining_received} unit(s) would "
                        "remain received."
                    )
                }
            )

        locked_line.delete()