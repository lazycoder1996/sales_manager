from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import SellerPayment


class SellerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPayment

        fields = [
            "id",
            "seller",
            "amount",
            "paid_at",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value