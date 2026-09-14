from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.services.stock_balance import (
    StockBalanceService,
)


class StockBalanceView(APIView):

    def get(self, request):
        product_id = request.query_params.get("product")
        variant_id = request.query_params.get("variant")

        balance = StockBalanceService.get_balance(
            product_id=product_id,
            variant_id=variant_id,
        )

        return APIResponse.success(
            data=balance,
            message="Stock balance retrieved successfully.",
        )