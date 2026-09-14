from rest_framework import serializers

from apps.inventory.models import StockReceiptLine


class StockReceiptLineSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        required=False,
    )

    _delete = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
    )

    class Meta:
        model = StockReceiptLine
        fields = [
            "id",
            "stock_receipt",
            "product",
            "product_variant",
            "quantity",
            "unit_cost",
            "_delete",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "stock_receipt",
            "unit_cost",
            "created_at",
            "updated_at",
        ]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        return value

    def validate(self, attrs):
        line_id = attrs.get("id")
        delete = attrs.get("_delete", False)

        # Deletion requires an existing line ID.
        if delete:
            if not line_id:
                raise serializers.ValidationError({
                    "id": "An existing line ID is required for deletion."
                })

            return attrs

        # New line: product and quantity are required.
        if not line_id:
            if "product" not in attrs:
                raise serializers.ValidationError({
                    "product": "This field is required for a new line."
                })

            if "quantity" not in attrs:
                raise serializers.ValidationError({
                    "quantity": "This field is required for a new line."
                })

        return attrs