from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import Product, ProductVariant


class AdditionalPurchaseLineSerializer(
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


class AdditionalPurchaseSerializer(
    serializers.Serializer
):
    lines = AdditionalPurchaseLineSerializer(
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