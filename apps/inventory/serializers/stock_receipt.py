from rest_framework import serializers

from apps.inventory.models import StockReceipt
from .stock_receipt_line import StockReceiptLineSerializer


class StockReceiptSerializer(serializers.ModelSerializer):
    lines = StockReceiptLineSerializer(
        many=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = StockReceipt
        fields = [
            "id",
            "seller",
            "source",
            "received_at",
            "notes",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_source(self, value):
        if value not in [
            StockReceipt.Source.OWNER_SUPPLIED,
            StockReceipt.Source.PURCHASED_ON_BEHALF,
        ]:
            raise serializers.ValidationError(
                "Invalid stock receipt source"
            )

        return value

    def validate_lines(self, lines):
        combinations = set()

        for line in lines:
            if line.get("_delete"):
                continue

            product = line.get("product")
            product_variant = line.get("product_variant")

            # We only check duplicate combinations when enough
            # information is available.
            if product is not None:
                combination = (
                    product.id,
                    product_variant.id if product_variant else None,
                )

                if combination in combinations:
                    raise serializers.ValidationError(
                        "The same product/variant cannot appear "
                        "more than once in the same request."
                    )

                combinations.add(combination)

        return lines