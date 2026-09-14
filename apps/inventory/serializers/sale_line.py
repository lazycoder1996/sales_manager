from rest_framework import serializers

from apps.inventory.models import SaleLine


class SaleLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    product_variant_size = serializers.CharField(
        source="product_variant.size",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SaleLine

        fields = [
            "id",
            "product",
            "product_name",
            "product_variant",
            "product_variant_size",
            "quantity",
            "delivered_quantity",
            "unit_price",
            "unit_cost",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "product_variant_size",
            "delivered_quantity",
            "unit_price",
            "unit_cost",
            "created_at",
            "updated_at",
        ]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Quantity must be at least 1."
            )

        return value