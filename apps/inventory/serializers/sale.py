from rest_framework import serializers

from apps.inventory.models import Sale
from apps.inventory.serializers.sale_line import (
    SaleLineSerializer,
)
from apps.inventory.services.sale import SaleService


class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(
        many=True,
        read_only=True,
    )

    total = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    outstanding_amount = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()

    class Meta:
        model = Sale

        fields = [
            "id",
            "student_number",
            "student_name",
            "sold_at",
            "notes",
            "total",
            "paid_amount",
            "outstanding_amount",
            "payment_status",
            "delivery_status",
            "lines",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "total",
            "paid_amount",
            "outstanding_amount",
            "payment_status",
            "delivery_status",
            "lines",
            "created_at",
            "updated_at",
        ]

    def get_total(self, sale):
        return SaleService.get_total(sale)

    def get_paid_amount(self, sale):
        return SaleService.get_paid_amount(sale)

    def get_outstanding_amount(self, sale):
        return SaleService.get_outstanding_amount(sale)

    def get_payment_status(self, sale):
        return SaleService.get_payment_status(sale)

    def get_delivery_status(self, sale):
        return SaleService.get_delivery_status(sale)