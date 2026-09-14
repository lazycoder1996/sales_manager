from rest_framework import serializers


class DeliveryLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class DeliverySerializer(serializers.Serializer):
    lines = DeliveryLineSerializer(
        many=True,
        allow_empty=False,
    )