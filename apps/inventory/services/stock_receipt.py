from django.db import transaction
from rest_framework import serializers

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
                product_variant=line_data.get("product_variant"),
                quantity=line_data["quantity"],
            )

        return receipt

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
        # A receipt's seller cannot be changed once any stock from
        # the receipt has been allocated to sales.
        if seller is not None and seller != receipt.seller:
            has_allocated_stock = receipt.lines.filter(
                sale_allocations__isnull=False,
            ).exists()

            if has_allocated_stock:
                raise serializers.ValidationError(
                    "Seller cannot be changed because stock from "
                    "this receipt has already been allocated to sales."
                )

            if not seller.is_active:
                raise serializers.ValidationError(
                    "Seller is inactive."
                )

            receipt.seller = seller

        if source is not None:
            receipt.source = source

        if received_at is not None:
            receipt.received_at = received_at

        if notes is not None:
            receipt.notes = notes

        receipt.save(
            update_fields=[
                "seller",
                "source",
                "received_at",
                "notes",
                "updated_at",
            ],
        )

        if lines is not None:
            for line_data in lines:
                line_id = line_data.get("id")
                should_delete = line_data.get(
                    "_delete",
                    False,
                )

                # Delete existing line.
                if should_delete:
                    line = receipt.lines.filter(
                        id=line_id,
                    ).first()

                    if line is None:
                        raise serializers.ValidationError(
                            f"Stock receipt line {line_id} was not found."
                        )

                    StockReceiptLineService.delete(line)

                    continue

                # Update existing line.
                if line_id:
                    line = receipt.lines.filter(
                        id=line_id,
                    ).first()

                    if line is None:
                        raise serializers.ValidationError(
                            f"Stock receipt line {line_id} was not found."
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
                        update_product="product" in line_data,
                        update_product_variant=(
                            "product_variant" in line_data
                        ),
                        update_quantity="quantity" in line_data,
                    )

                    continue

                # Create new line.
                if "product" not in line_data:
                    raise serializers.ValidationError(
                        "Product is required for a new receipt line."
                    )

                if "quantity" not in line_data:
                    raise serializers.ValidationError(
                        "Quantity is required for a new receipt line."
                    )

                StockReceiptLineService.create(
                    stock_receipt=receipt,
                    product=line_data["product"],
                    product_variant=line_data.get(
                        "product_variant",
                    ),
                    quantity=line_data["quantity"],
                )

        return receipt