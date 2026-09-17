from rest_framework.views import APIView

from apps.core.responses import APIResponse

from apps.inventory.serializers.house import (
    HouseSerializer,
)
from apps.inventory.services.house import (
    HouseService,
)


class HouseListView(APIView):

    def get(self, request):
        houses = HouseService.get_houses()

        serializer = HouseSerializer(
            houses,
            many=True,
        )

        return APIResponse.success(
            data=serializer.data,
            message="Houses retrieved successfully.",
        )


class HouseDetailView(APIView):

    def get(self, request, house_id):
        house = HouseService.get_house(
            house_id
        )

        if house is None:
            return APIResponse.error(
                message="House not found.",
                status_code=404,
            )

        serializer = HouseSerializer(
            house
        )

        return APIResponse.success(
            data=serializer.data,
            message="House retrieved successfully.",
        )