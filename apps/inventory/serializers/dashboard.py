from rest_framework import serializers


class DashboardStockSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product = serializers.CharField()
    variant_id = serializers.UUIDField(
        allow_null=True,
    )
    variant = serializers.CharField(
        allow_null=True,
    )
    received = serializers.IntegerField()
    delivered = serializers.IntegerField()
    available = serializers.IntegerField()


class DashboardEarningSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product = serializers.CharField()
    variant_id = serializers.UUIDField(
        allow_null=True,
    )
    variant = serializers.CharField(
        allow_null=True,
    )
    quantity = serializers.IntegerField()
    revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    earnings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )


class DashboardSalesSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    total_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )


class DashboardPaymentsSerializer(serializers.Serializer):
    total_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    outstanding = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )


class DashboardDeliverySerializer(serializers.Serializer):
    awaiting_delivery = serializers.IntegerField()
    partially_delivered = serializers.IntegerField()


class DashboardSellerSerializer(serializers.Serializer):
    seller_id = serializers.UUIDField()
    seller = serializers.CharField()
    total_owed = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    total_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    outstanding = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )


class DashboardSellersSerializer(serializers.Serializer):
    total_owed = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    total_paid = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    outstanding = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    sellers = DashboardSellerSerializer(
        many=True,
    )


class DashboardEarningsSerializer(serializers.Serializer):
    revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    earnings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    products = DashboardEarningSerializer(
        many=True,
    )


class DashboardSerializer(serializers.Serializer):
    sales = DashboardSalesSerializer()
    payments = DashboardPaymentsSerializer()
    delivery = DashboardDeliverySerializer()
    stock = DashboardStockSerializer(
        many=True,
    )
    sellers = DashboardSellersSerializer()
    earnings = DashboardEarningsSerializer()