from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment

        fields = [
            "id",
            "sale",
            "cash_amount",
            "momo_amount",
            "amount",
            "paid_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "amount",
            "created_at",
            "updated_at",
        ]

    def validate_cash_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Cash amount cannot be negative."
            )

        return value

    def validate_momo_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "MoMo amount cannot be negative."
            )

        return value

    def validate(self, attrs):
        cash_amount = attrs.get(
            "cash_amount",
            Decimal("0"),
        )

        momo_amount = attrs.get(
            "momo_amount",
            Decimal("0"),
        )

        if cash_amount + momo_amount <= 0:
            raise serializers.ValidationError({
                "cash_amount": (
                    "Payment amount must be greater "
                    "than zero."
                )
            })

        return attrs