from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Sale, SaleLine
from apps.inventory.serializers.sale_line import (
    SaleLineSerializer,
)
from apps.inventory.services.sale_line import (
    SaleLineService,
)


class SaleLineCreateView(APIView):

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

        serializer = SaleLineSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        line = SaleLineService.create(
            sale=sale,
            product=serializer.validated_data[
                "product"
            ],
            product_variant=serializer.validated_data.get(
                "product_variant"
            ),
            quantity=serializer.validated_data[
                "quantity"
            ],
        )

        return APIResponse.success(
            data=SaleLineSerializer(line).data,
            message="Sale line added successfully.",
            status_code=201,
        )


class SaleLineDetailView(APIView):

    def patch(
        self,
        request,
        sale_id,
        line_id,
    ):
        try:
            line = (
                SaleLine.objects
                .select_related(
                    "sale",
                    "product",
                    "product_variant",
                )
                .get(
                    id=line_id,
                    sale_id=sale_id,
                )
            )
        except SaleLine.DoesNotExist:
            return APIResponse.error(
                message="Sale line not found.",
                status_code=404,
            )

        serializer = SaleLineSerializer(
            line,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        line = SaleLineService.update(
            line=line,
            quantity=serializer.validated_data[
                "quantity"
            ],
        )

        return APIResponse.success(
            data=SaleLineSerializer(line).data,
            message="Sale line updated successfully.",
        )

    def delete(
        self,
        request,
        sale_id,
        line_id,
    ):
        try:
            line = SaleLine.objects.get(
                id=line_id,
                sale_id=sale_id,
            )
        except SaleLine.DoesNotExist:
            return APIResponse.error(
                message="Sale line not found.",
                status_code=404,
            )

        SaleLineService.delete(line)

        return APIResponse.success(
            message="Sale line deleted successfully.",
        )