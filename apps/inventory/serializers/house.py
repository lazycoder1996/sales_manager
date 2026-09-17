from rest_framework import serializers

from apps.inventory.models import House


class HouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = House
        fields = [
            "id",
            "name",
            "code",
            "gender",
            "color",
            "partner_house",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]