from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import Product
from apps.inventory.models import ProductVariant


class CompleteSaleLineSerializer(
    serializers.Serializer
):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )

    product_variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        required=False,
        allow_null=True,
    )

    quantity = serializers.IntegerField(
        min_value=1
    )


class CompleteSaleSerializer(
    serializers.Serializer
):
    student_number = serializers.CharField(
        max_length=50
    )

    student_name = serializers.CharField(
        max_length=255
    )

    sold_at = serializers.DateTimeField()

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    lines = CompleteSaleLineSerializer(
        many=True,
        allow_empty=False,
    )

    cash_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
    )

    momo_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
    )

    paid_at = serializers.DateTimeField()

    def validate_student_number(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Student number is required."
            )

        return value

    def validate_student_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Student name is required."
            )

        return value