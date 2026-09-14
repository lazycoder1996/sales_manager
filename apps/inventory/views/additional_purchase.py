from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Sale
from apps.inventory.serializers.additional_purchase import (
    AdditionalPurchaseSerializer,
)
from apps.inventory.serializers.sale_line import (
    SaleLineSerializer,
)
from apps.inventory.services.additional_purchase import (
    AdditionalPurchaseService,
)


class AdditionalPurchaseCreateView(APIView):

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

        serializer = AdditionalPurchaseSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        lines = (
            AdditionalPurchaseService.create(
                sale=sale,
                lines=serializer.validated_data[
                    "lines"
                ],
                cash_amount=serializer.validated_data[
                    "cash_amount"
                ],
                momo_amount=serializer.validated_data[
                    "momo_amount"
                ],
                paid_at=serializer.validated_data[
                    "paid_at"
                ],
            )
        )

        return APIResponse.success(
            data=SaleLineSerializer(
                lines,
                many=True,
            ).data,
            message=(
                "Additional purchase recorded "
                "successfully."
            ),
            status_code=201,
        )