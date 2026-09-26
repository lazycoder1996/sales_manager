from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField
from django.db.models import F
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import SaleLine
from apps.inventory.models import SellerPayment
from apps.inventory.models.stock_receipt_line import StockReceiptLine


class SellerPaymentService:

    @staticmethod
    def get_seller_product_ids(seller):
        """
        Return the distinct product IDs that belong to this seller.

        A seller's products are determined from the products supplied
        through the seller's stock receipt lines.
        """

        return (
            StockReceiptLine.objects
            .filter(
                stock_receipt__seller=seller,
            )
            .values("product_id")
            .distinct()
        )

    @staticmethod
    def get_seller_total_owed(seller):
        """
        Calculate the total amount currently owed to the seller.

        Seller ownership is determined by the distinct products that
        appear on the seller's stock receipt lines.

        Owed amount is based on sold quantities only:

            sale_line.quantity × sale_line.unit_cost

        Delivered quantity, physical stock, and stock allocations
        do not affect seller accounting.
        """

        product_ids = (
            SellerPaymentService
            .get_seller_product_ids(seller)
        )

        return (
            SaleLine.objects
            .filter(
                product_id__in=product_ids,
            )
            .aggregate(
                total=Sum(
                    F("quantity") * F("unit_cost"),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
            )["total"]
            or Decimal("0.00")
        )

    @staticmethod
    def get_seller_total_paid(seller):
        """
        Return the total amount paid to the seller.
        """

        return (
            SellerPayment.objects
            .filter(
                seller=seller,
            )
            .aggregate(
                total=Sum("amount"),
            )["total"]
            or Decimal("0.00")
        )

    @staticmethod
    def get_seller_outstanding(seller):
        """
        Calculate the seller's outstanding balance.

        outstanding = total owed - total paid
        """

        owed = (
            SellerPaymentService
            .get_seller_total_owed(seller)
        )

        paid = (
            SellerPaymentService
            .get_seller_total_paid(seller)
        )

        return max(
            owed - paid,
            Decimal("0.00"),
        )

    @staticmethod
    @transaction.atomic
    def create(
        seller,
        amount,
        paid_at,
        notes="",
    ):
        if not seller.is_active:
            raise serializers.ValidationError(
                "Seller is inactive."
            )

        if amount <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        outstanding = (
            SellerPaymentService
            .get_seller_outstanding(seller)
        )

        if amount > outstanding:
            raise serializers.ValidationError(
                f"Payment cannot exceed the seller's outstanding "
                f"balance of {outstanding}."
            )

        payment = SellerPayment.objects.create(
            seller=seller,
            amount=amount,
            paid_at=paid_at,
            notes=notes,
        )

        return payment