from rest_framework import serializers


class StockDetailReceiptSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    seller = serializers.CharField()
    source = serializers.CharField()

    quantity = serializers.IntegerField()
    unit_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    receipt_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    receipt_paid = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    receipt_outstanding = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    receipt_payment_status = serializers.CharField()

    received_at = serializers.DateTimeField()
    notes = serializers.CharField()


class StockDetailSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product = serializers.CharField()

    variant_id = serializers.UUIDField(
        allow_null=True,
    )

    variant = serializers.CharField(
        allow_null=True,
    )

    stock = serializers.DictField()

    receipts = StockDetailReceiptSerializer(
        many=True,
    )