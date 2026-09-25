from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import Product
from apps.inventory.models import ProductVariant
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


class ChangeProductItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            is_active=True
        ),
    )

    product_variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.filter(
            is_active=True
        ),
        required=False,
        allow_null=True,
    )

    quantity = serializers.IntegerField(
        min_value=1,
    )

    def validate(self, attrs):
        product = attrs["product"]
        product_variant = attrs.get(
            "product_variant"
        )

        active_variants = product.variants.filter(
            is_active=True
        )

        if (
            active_variants.exists()
            and product_variant is None
        ):
            raise serializers.ValidationError(
                {
                    "product_variant": (
                        "A variant is required for this product."
                    )
                }
            )

        if (
            not active_variants.exists()
            and product_variant is not None
        ):
            raise serializers.ValidationError(
                {
                    "product_variant": (
                        "This product does not have variants."
                    )
                }
            )

        if (
            product_variant is not None
            and product_variant.product_id
            != product.id
        ):
            raise serializers.ValidationError(
                {
                    "product_variant": (
                        "The selected variant does not belong "
                        "to the selected product."
                    )
                }
            )

        return attrs


class ChangeProductSerializer(serializers.Serializer):
    return_quantity = serializers.IntegerField(
        min_value=1,
    )

    items = ChangeProductItemSerializer(
        many=True,
        allow_empty=False,
    )

    cash_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )

    momo_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )

    def validate_items(self, items):
        identities = set()

        for item in items:
            product = item["product"]
            product_variant = item.get(
                "product_variant"
            )

            identity = (
                product.id,
                (
                    product_variant.id
                    if product_variant is not None
                    else None
                ),
            )

            if identity in identities:
                raise serializers.ValidationError(
                    (
                        "The same product and variant cannot "
                        "appear more than once in the "
                        "replacement items. Increase its "
                        "quantity instead."
                    )
                )

            identities.add(identity)

        return items

    def validate(self, attrs):
        cash_amount = attrs.get(
            "cash_amount",
            Decimal("0.00"),
        )

        momo_amount = attrs.get(
            "momo_amount",
            Decimal("0.00"),
        )

        attrs["cash_amount"] = cash_amount
        attrs["momo_amount"] = momo_amount

        return attrs


class ReturnSaleLineSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
    )