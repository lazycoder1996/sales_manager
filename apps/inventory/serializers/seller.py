from django.db.models import Sum
from rest_framework import serializers

from apps.inventory.models import Seller
from apps.inventory.models.stock_receipt_line import (
    StockReceiptLine,
)
from apps.inventory.services.seller_payment import (
    SellerPaymentService,
)


class SellerSerializer(serializers.ModelSerializer):
    total_owed = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding = serializers.SerializerMethodField()
    stock_supplied = serializers.SerializerMethodField()

    class Meta:
        model = Seller

        fields = [
            "id",
            "name",
            "phone",
            "notes",
            "is_active",
            "total_owed",
            "total_paid",
            "outstanding",
            "stock_supplied",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "total_owed",
            "total_paid",
            "outstanding",
            "stock_supplied",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Seller name is required."
            )

        return value

    def get_total_owed(self, seller):
        return SellerPaymentService.get_seller_total_owed(
            seller,
        )

    def get_total_paid(self, seller):
        return SellerPaymentService.get_seller_total_paid(
            seller,
        )

    def get_outstanding(self, seller):
        return SellerPaymentService.get_seller_outstanding(
            seller,
        )

    def get_stock_supplied(self, seller):
        return (
            StockReceiptLine.objects
            .filter(
                stock_receipt__seller=seller,
            )
            .aggregate(
                total=Sum("quantity"),
            )["total"]
            or 0
        )