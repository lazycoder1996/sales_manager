from rest_framework import serializers

from apps.inventory.models import Product
from .product_variant import (
    ProductVariantSerializer,
)


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "cost_price",
            "selling_price",
            "required",
            "required_quantity",
            "is_active",
            "variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "variants",
            "created_at",
            "updated_at",
        ]
    def validate(self, attrs):
        if self.instance:
            # Update operation
            if "cost_price" in attrs and attrs["cost_price"] < 0:
                raise serializers.ValidationError({
                    "cost_price": "Cost price must be a non-negative value."
                })
            if "selling_price" in attrs and attrs["selling_price"] < 0:
                raise serializers.ValidationError({
                    "selling_price": "Selling price must be a non-negative value."
                })
            if "required_quantity" in attrs and attrs["required_quantity"] < 0:
                raise serializers.ValidationError({
                    "required_quantity": "Required quantity must be a non-negative value."
                })
        else:
            # Create operation
            if attrs.get("cost_price", 0) < 0:
                raise serializers.ValidationError({
                    "cost_price": "Cost price must be a non-negative value."
                })
            if attrs.get("selling_price", 0) < 0:
                raise serializers.ValidationError({
                    "selling_price": "Selling price must be a non-negative value."
                })
            if attrs.get("required_quantity", 0) < 0:
                raise serializers.ValidationError({
                    "required_quantity": "Required quantity must be a non-negative value."
                })
                

        return super().validate(attrs)