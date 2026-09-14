from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Sale
from apps.inventory.serializers.delivery import (
    DeliverySerializer,
)
from apps.inventory.serializers.sale import SaleSerializer
from apps.inventory.services.delivery import (
    DeliveryService,
)


class SaleDeliveryView(APIView):

    def post(self, request, sale_id):
        try:
            sale = Sale.objects.get(
                id=sale_id
            )
        except Sale.DoesNotExist:
            return APIResponse.error(
                message="Sale not found.",
                status_code=404,
            )

        serializer = DeliverySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        DeliveryService.deliver(
            sale=sale,
            lines=serializer.validated_data[
                "lines"
            ],
        )

        sale = (
            Sale.objects
            .prefetch_related(
                "lines",
                "lines__product",
                "lines__product_variant",
            )
            .get(id=sale_id)
        )

        return APIResponse.success(
            data=SaleSerializer(sale).data,
            message="Items delivered successfully.",
        )