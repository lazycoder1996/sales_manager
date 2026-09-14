from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.serializers.dashboard import (
    DashboardSerializer,
)
from apps.inventory.services.dashboard import (
    DashboardService,
)


class DashboardView(APIView):

    def get(self, request):
        data = DashboardService.get_dashboard()

        serializer = DashboardSerializer(data)

        return APIResponse.success(
            data=serializer.data,
            message="Dashboard retrieved successfully.",
        )