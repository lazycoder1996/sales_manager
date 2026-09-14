from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import (
    Product,
    ProductVariant,
    SaleLine,
    StockReceiptLine,
)
from apps.inventory.services.seller_payment import (
    SellerPaymentService,
)


class StockDetailService:

    @staticmethod
    def get_detail(
        product_id=None,
        variant_id=None,
    ):
        product = (
            Product.objects
            .filter(id=product_id)
            .first()
        )

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
                    product_id=product.id,
                )
                .first()
            )

            if variant is None:
                raise serializers.ValidationError({
                    "variant": (
                        "Product variant not found "
                        "for this product."
                    )
                })

        variant_id_filter = (
            variant.id
            if variant is not None
            else None
        )

        receipt_queryset = (
            StockReceiptLine.objects
            .select_related(
                "stock_receipt",
                "stock_receipt__seller",
            )
            .filter(
                product_id=product.id,
                product_variant_id=variant_id_filter,
            )
            .order_by(
                "-stock_receipt__received_at",
                "-created_at",
            )
        )

        received = (
            receipt_queryset
            .aggregate(
                total=Sum("quantity"),
            )["total"]
            or 0
        )

        delivered = (
            SaleLine.objects
            .filter(
                product_id=product.id,
                product_variant_id=variant_id_filter,
                delivered_quantity__gt=0,
            )
            .aggregate(
                total=Sum("delivered_quantity"),
            )["total"]
            or 0
        )

        receipts = []

        seen_receipts = set()

        for line in receipt_queryset:
            receipt = line.stock_receipt

            # A receipt can contain multiple lines.
            # We only want to calculate its financial
            # information once.
            if receipt.id in seen_receipts:
                continue

            seen_receipts.add(receipt.id)

            receipt_total = (
                SellerPaymentService
                .get_receipt_total(receipt)
            )

            receipt_paid = (
                SellerPaymentService
                .get_receipt_paid_amount(receipt)
            )

            receipt_paid = min(
                receipt_paid,
                receipt_total,
            )

            receipt_outstanding = (
                receipt_total - receipt_paid
            )

            if receipt_paid <= 0:
                payment_status = "unpaid"
            elif receipt_paid < receipt_total:
                payment_status = "partially_paid"
            else:
                payment_status = "paid"

            receipts.append({
                "id": receipt.id,
                "seller": receipt.seller.name,
                "source": receipt.source,

                # This is the quantity of this particular
                # product/variant on the receipt.
                "quantity": line.quantity,
                "unit_cost": line.unit_cost,

                # These are receipt-level financial values.
                "receipt_total": receipt_total,
                "receipt_paid": receipt_paid,
                "receipt_outstanding": (
                    receipt_outstanding
                ),
                "receipt_payment_status": (
                    payment_status
                ),

                "received_at": receipt.received_at,
                "notes": receipt.notes,
            })

        return {
            "product_id": product.id,
            "product": product.name,

            "variant_id": (
                variant.id
                if variant is not None
                else None
            ),

            "variant": (
                variant.size
                if variant is not None
                else None
            ),

            "stock": {
                "received": received,
                "delivered": delivered,
                "available": received - delivered,
            },

            "receipts": receipts,
        }