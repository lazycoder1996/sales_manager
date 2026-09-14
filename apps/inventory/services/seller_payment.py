from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import (
    SellerPayment,
    SellerPaymentAllocation,
    StockReceipt,
    StockReceiptLine,
)


class SellerPaymentService:

    @staticmethod
    def get_receipt_total(receipt):
        lines = (
            StockReceiptLine.objects
            .filter(
                stock_receipt=receipt,
            )
        )

        return sum(
            (
                line.quantity * line.unit_cost
                for line in lines
            ),
            Decimal("0"),
        )

    @staticmethod
    def get_receipt_paid_amount(receipt):
        return (
            SellerPaymentAllocation.objects
            .filter(
                stock_receipt=receipt,
            )
            .aggregate(
                total=Sum("amount"),
            )["total"]
            or Decimal("0")
        )

    @staticmethod
    def get_receipt_outstanding(receipt):
        total = SellerPaymentService.get_receipt_total(
            receipt,
        )

        paid = SellerPaymentService.get_receipt_paid_amount(
            receipt,
        )

        outstanding = total - paid

        return max(
            outstanding,
            Decimal("0"),
        )

    @staticmethod
    def get_receipt_payment_status(receipt):
        total = SellerPaymentService.get_receipt_total(
            receipt,
        )

        if total <= 0:
            return "unpaid"

        paid = SellerPaymentService.get_receipt_paid_amount(
            receipt,
        )

        if paid <= 0:
            return "unpaid"

        if paid < total:
            return "partially_paid"

        return "paid"

    @staticmethod
    def get_seller_total_owed(seller):
        receipts = StockReceipt.objects.filter(
            seller=seller,
        )

        total = Decimal("0")

        for receipt in receipts:
            total += SellerPaymentService.get_receipt_total(
                receipt,
            )

        return total

    @staticmethod
    def get_seller_total_paid(seller):
        return (
            SellerPayment.objects
            .filter(
                seller=seller,
            )
            .aggregate(
                total=Sum("amount"),
            )["total"]
            or Decimal("0")
        )

    @staticmethod
    def get_seller_outstanding(seller):
        owed = SellerPaymentService.get_seller_total_owed(
            seller,
        )

        paid = SellerPaymentService.get_seller_total_paid(
            seller,
        )

        return max(
            owed - paid,
            Decimal("0"),
        )

    @staticmethod
    @transaction.atomic
    def create(
        seller,
        amount,
        paid_at,
        notes="",
    ):
        amount = Decimal(amount)

        if amount <= 0:
            raise serializers.ValidationError({
                "amount": (
                    "Payment amount must be greater than zero."
                )
            })

        if not seller.is_active:
            raise serializers.ValidationError({
                "seller": (
                    "The selected seller is inactive."
                )
            })

        outstanding = (
            SellerPaymentService
            .get_seller_outstanding(seller)
        )

        if outstanding <= 0:
            raise serializers.ValidationError({
                "seller": (
                    "This seller has no outstanding balance."
                )
            })

        if amount > outstanding:
            raise serializers.ValidationError({
                "amount": (
                    f"Payment cannot exceed the seller's "
                    f"outstanding balance of "
                    f"GHS {outstanding:.2f}."
                )
            })

        payment = SellerPayment.objects.create(
            seller=seller,
            amount=amount,
            paid_at=paid_at,
            notes=notes,
        )

        remaining_payment = amount

        receipts = (
            StockReceipt.objects
            .filter(
                seller=seller,
            )
            .order_by(
                "received_at",
                "created_at",
            )
        )

        for receipt in receipts:
            if remaining_payment <= 0:
                break

            receipt_outstanding = (
                SellerPaymentService
                .get_receipt_outstanding(receipt)
            )

            if receipt_outstanding <= 0:
                continue

            allocation_amount = min(
                remaining_payment,
                receipt_outstanding,
            )

            SellerPaymentAllocation.objects.create(
                seller_payment=payment,
                stock_receipt=receipt,
                amount=allocation_amount,
            )

            remaining_payment -= allocation_amount

        return payment