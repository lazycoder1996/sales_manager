from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Sale


class SaleService:

    @staticmethod
    def get_total(sale):
        return sum(
            (
                line.quantity * line.unit_price
                for line in sale.lines.all()
            ),
            Decimal("0"),
        )

    @staticmethod
    def get_paid_amount(sale):
        return sum(
            (
                payment.amount
                for payment in sale.payments.all()
            ),
            Decimal("0"),
        )

    @staticmethod
    def get_outstanding_amount(sale):
        total = SaleService.get_total(sale)
        paid = SaleService.get_paid_amount(sale)

        outstanding = total - paid

        if outstanding < 0:
            return Decimal("0")

        return outstanding

    @staticmethod
    def get_payment_status(sale):
        total = SaleService.get_total(sale)

        if total <= 0:
            return "unpaid"

        paid = SaleService.get_paid_amount(sale)

        if paid <= 0:
            return "unpaid"

        if paid < total:
            return "partially_paid"

        return "paid"

    @staticmethod
    def get_delivery_status(sale):
        lines = list(
            sale.lines.all()
        )

        if not lines:
            return "undelivered"

        total_quantity = sum(
            line.quantity
            for line in lines
        )

        total_delivered_quantity = sum(
            line.delivered_quantity
            for line in lines
        )

        if total_delivered_quantity == 0:
            return "undelivered"

        if total_delivered_quantity >= total_quantity:
            return "delivered"

        return "partially_delivered"

    @staticmethod
    @transaction.atomic
    def create(
        student_number,
        student_name,
        sold_at,
        notes="",
    ):
        if Sale.objects.filter(
            student_number=student_number
        ).exists():
            raise serializers.ValidationError({
                "student_number": (
                    "A sale already exists for "
                    "this student."
                )
            })

        return Sale.objects.create(
            student_number=student_number,
            student_name=student_name,
            sold_at=sold_at,
            notes=notes,
        )

    @staticmethod
    @transaction.atomic
    def create_with_payment(
        student_number,
        student_name,
        sold_at,
        lines,
        cash_amount,
        momo_amount,
        paid_at,
        notes="",
    ):
        from apps.inventory.services.payment import (
            PaymentService,
        )
        from apps.inventory.services.sale_line import (
            SaleLineService,
        )

        if not lines:
            raise serializers.ValidationError({
                "lines": (
                    "A sale must contain at least "
                    "one item."
                )
            })

        cash_amount = Decimal(
            cash_amount
        )

        momo_amount = Decimal(
            momo_amount
        )

        if cash_amount < 0:
            raise serializers.ValidationError({
                "cash_amount": (
                    "Cash amount cannot be negative."
                )
            })

        if momo_amount < 0:
            raise serializers.ValidationError({
                "momo_amount": (
                    "MoMo amount cannot be negative."
                )
            })

        payment_amount = (
            cash_amount + momo_amount
        )

        if payment_amount <= 0:
            raise serializers.ValidationError({
                "amount": (
                    "Payment amount must be "
                    "greater than zero."
                )
            })

        sale = SaleService.create(
            student_number=student_number,
            student_name=student_name,
            sold_at=sold_at,
            notes=notes,
        )

        for line in lines:
            SaleLineService.create(
                sale=sale,
                product=line["product"],
                product_variant=line.get(
                    "product_variant"
                ),
                quantity=line["quantity"],
            )

        sale_total = SaleService.get_total(
            sale
        )

        if payment_amount != sale_total:
            raise serializers.ValidationError({
                "amount": (
                    f"Payment must equal the "
                    f"sale total of GHS "
                    f"{sale_total:.2f}."
                )
            })

        PaymentService.create(
            sale=sale,
            cash_amount=cash_amount,
            momo_amount=momo_amount,
            paid_at=paid_at,
        )

        return sale

    @staticmethod
    @transaction.atomic
    def update(
        sale,
        student_name=None,
        sold_at=None,
        notes=None,
    ):
        if student_name is not None:
            sale.student_name = student_name

        if sold_at is not None:
            sale.sold_at = sold_at

        if notes is not None:
            sale.notes = notes

        sale.save(
            update_fields=[
                "student_name",
                "sold_at",
                "notes",
                "updated_at",
            ]
        )

        return sale