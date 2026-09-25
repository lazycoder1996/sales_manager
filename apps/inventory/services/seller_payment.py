from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import SellerPayment
from apps.inventory.services.stock_allocation import (
    StockAllocationService,
)


class SellerPaymentService:

    @staticmethod
    def get_seller_total_owed(seller):
        """
        Total amount currently owed to the seller based on sold units
        allocated to this seller's stock receipt layers.

        Stock that has merely been received is NOT owed yet.
        """

        return StockAllocationService.get_seller_total_owed(
            seller,
        )

    @staticmethod
    def get_seller_total_paid(seller):
        return (
            SellerPayment.objects
            .filter(seller=seller)
            .aggregate(
                total=Sum("amount"),
            )["total"]
            or Decimal("0.00")
        )

    @staticmethod
    def get_seller_outstanding(seller):
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