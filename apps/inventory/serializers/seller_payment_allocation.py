from decimal import Decimal

from rest_framework import serializers


class SellerPaymentAllocationItemSerializer(
    serializers.Serializer
):
    stock_receipt_id = serializers.UUIDField()

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )


class SellerPaymentAllocationSerializer(
    serializers.Serializer
):
    allocations = SellerPaymentAllocationItemSerializer(
        many=True,
        allow_empty=False,
    )