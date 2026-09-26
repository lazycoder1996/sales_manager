from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import SaleLine
from apps.inventory.models import StockReceipt
from apps.inventory.services.stock_receipt_line import (
    StockReceiptLineService,
)


class StockReceiptService:

    @staticmethod
    @transaction.atomic
    def create(
        seller,
        source,
        received_at,
        notes,
        lines,
    ):
        if not seller.is_active:
            raise serializers.ValidationError(
                "Seller is inactive."
            )

        receipt = StockReceipt.objects.create(
            seller=seller,
            source=source,
            received_at=received_at,
            notes=notes,
        )

        for line_data in lines:
            StockReceiptLineService.create(
                stock_receipt=receipt,
                product=line_data["product"],
                product_variant=line_data.get(
                    "product_variant",
                ),
                quantity=line_data["quantity"],
            )

        return receipt

    @staticmethod
    def _receipt_products_have_sales(receipt):
        """
        Determine whether any product supplied by this receipt
        has already appeared on a sale.

        Seller ownership is now determined from:

            seller
                ↓
            stock receipt lines
                ↓
            product IDs
                ↓
            sale lines

        Therefore changing the seller of a receipt after one of
        its products has been sold could change historical seller
        accounting.

        We prevent that change once a product from the receipt
        has appeared on a sale.
        """

        product_ids = (
            receipt.lines
            .values("product_id")
            .distinct()
        )

        return SaleLine.objects.filter(
            product_id__in=product_ids,
        ).exists()

    @staticmethod
    @transaction.atomic
    def update(
        receipt,
        source=None,
        seller=None,
        received_at=None,
        notes=None,
        lines=None,
    ):
        locked_receipt = (
            StockReceipt.objects
            .select_for_update()
            .get(pk=receipt.pk)
        )

        # ---------------------------------------------------------
        # Seller
        # ---------------------------------------------------------

        if (
            seller is not None
            and seller != locked_receipt.seller
        ):
            if not seller.is_active:
                raise serializers.ValidationError(
                    "Seller is inactive."
                )

            if StockReceiptService._receipt_products_have_sales(
                locked_receipt,
            ):
                raise serializers.ValidationError(
                    {
                        "seller": (
                            "Seller cannot be changed because "
                            "a product from this receipt has "
                            "already been sold."
                        )
                    }
                )

            locked_receipt.seller = seller

        # ---------------------------------------------------------
        # Other receipt fields
        # ---------------------------------------------------------

        if source is not None:
            locked_receipt.source = source

        if received_at is not None:
            locked_receipt.received_at = received_at

        if notes is not None:
            locked_receipt.notes = notes

        locked_receipt.save(
            update_fields=[
                "seller",
                "source",
                "received_at",
                "notes",
                "updated_at",
            ],
        )

        # ---------------------------------------------------------
        # Receipt lines
        # ---------------------------------------------------------

        if lines is not None:
            for line_data in lines:
                line_id = line_data.get("id")

                should_delete = line_data.get(
                    "_delete",
                    False,
                )

                # -------------------------------------------------
                # Delete existing line.
                # -------------------------------------------------

                if should_delete:
                    if not line_id:
                        raise serializers.ValidationError(
                            "A receipt line ID is required "
                            "when deleting a line."
                        )

                    line = (
                        locked_receipt.lines
                        .filter(id=line_id)
                        .first()
                    )

                    if line is None:
                        raise serializers.ValidationError(
                            f"Stock receipt line {line_id} "
                            "was not found."
                        )

                    StockReceiptLineService.delete(
                        line,
                    )

                    continue

                # -------------------------------------------------
                # Update existing line.
                # -------------------------------------------------

                if line_id:
                    line = (
                        locked_receipt.lines
                        .filter(id=line_id)
                        .first()
                    )

                    if line is None:
                        raise serializers.ValidationError(
                            f"Stock receipt line {line_id} "
                            "was not found."
                        )

                    StockReceiptLineService.update(
                        line=line,
                        product=line_data.get(
                            "product",
                            line.product,
                        ),
                        product_variant=line_data.get(
                            "product_variant",
                            line.product_variant,
                        ),
                        quantity=line_data.get(
                            "quantity",
                            line.quantity,
                        ),
                        update_product=(
                            "product" in line_data
                        ),
                        update_product_variant=(
                            "product_variant" in line_data
                        ),
                        update_quantity=(
                            "quantity" in line_data
                        ),
                    )

                    continue

                # -------------------------------------------------
                # Create new line.
                # -------------------------------------------------

                if "product" not in line_data:
                    raise serializers.ValidationError(
                        "Product is required for a new receipt line."
                    )

                if "quantity" not in line_data:
                    raise serializers.ValidationError(
                        "Quantity is required for a new receipt line."
                    )

                StockReceiptLineService.create(
                    stock_receipt=locked_receipt,
                    product=line_data["product"],
                    product_variant=line_data.get(
                        "product_variant",
                    ),
                    quantity=line_data["quantity"],
                )

        return locked_receipt