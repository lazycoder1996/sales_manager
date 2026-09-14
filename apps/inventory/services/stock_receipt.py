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
            raise serializers.ValidationError({
                "seller": "The selected seller is inactive."
            })

        receipt = StockReceipt.objects.create(
            seller=seller,
            source=source,
            received_at=received_at,
            notes=notes,
        )

        for line in lines:
            StockReceiptLineService.create(
                stock_receipt=receipt,
                product=line["product"],
                product_variant=line.get("product_variant"),
                quantity=line["quantity"],
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
        if seller is not None:
            if not seller.is_active:
                raise serializers.ValidationError({
                    "seller": "The selected seller is inactive."
                })

            receipt.seller = seller

        if source is not None:
            receipt.source = source

        if received_at is not None:
            receipt.received_at = received_at

        if notes is not None:
            receipt.notes = notes

        receipt.save(
            update_fields=[
                "source",
                "received_at",
                "notes",
                "updated_at",
            ]
        )

        if lines is not None:
            for line_data in lines:
                line_id = line_data.get("id")
                should_delete = line_data.get("_delete", False)

                # -----------------------------------
                # DELETE EXISTING LINE
                # -----------------------------------
                if should_delete:
                    line = receipt.lines.filter(
                        id=line_id,
                    ).first()

                    if line:
                        StockReceiptLineService.delete(line)

                    continue

                # -----------------------------------
                # UPDATE EXISTING LINE
                # -----------------------------------
                if line_id:
                    line = receipt.lines.filter(
                        id=line_id,
                    ).first()

                    if line is None:
                        raise ValueError(
                            f"Stock receipt line '{line_id}' "
                            "does not belong to this receipt."
                        )

                    StockReceiptLineService.update(
                        line=line,
                        product=line_data.get("product"),
                        product_variant=line_data.get(
                            "product_variant"
                        ),
                        quantity=line_data.get("quantity"),
                        update_product="product" in line_data,
                        update_product_variant=(
                            "product_variant" in line_data
                        ),
                        update_quantity="quantity" in line_data,
                    )

                    continue

                # -----------------------------------
                # CREATE NEW LINE
                # -----------------------------------
                StockReceiptLineService.create(
                    stock_receipt=receipt,
                    product=line_data["product"],
                    product_variant=line_data.get(
                        "product_variant"
                    ),
                    quantity=line_data["quantity"],
                )

        return receipt