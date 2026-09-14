from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.serializers.stock_detail import (
    StockDetailSerializer,
)
from apps.inventory.services.stock_detail import (
    StockDetailService,
)


class StockDetailView(APIView):

    def get(self, request):
        product_id = request.query_params.get(
            "product"
        )

        variant_id = request.query_params.get(
            "variant"
        )

        if not product_id:
            return APIResponse.error(
                error={
                    "product": (
                        "Product is required."
                    )
                },
                message="Product is required.",
                status_code=400,
            )

        data = StockDetailService.get_detail(
            product_id=product_id,
            variant_id=variant_id,
        )

        serializer = StockDetailSerializer(data)

        return APIResponse.success(
            data=serializer.data,
            message=(
                "Stock detail retrieved successfully."
            ),
        )