from rest_framework import serializers


class DeliveryLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class DeliverySerializer(serializers.Serializer):
    lines = DeliveryLineSerializer(
        many=True,
        allow_empty=False,
    )


class UndeliveryLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UndeliverySerializer(serializers.Serializer):
    lines = UndeliveryLineSerializer(
        many=True,
        allow_empty=False,
    )