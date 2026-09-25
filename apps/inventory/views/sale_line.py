from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Sale
from apps.inventory.models import SaleLine
from apps.inventory.serializers.sale_line import (
    ChangeProductSerializer,
    ReturnSaleLineSerializer,
    SaleLineSerializer,
)
from apps.inventory.services.sale_line import SaleLineService


class SaleLineCreateView(APIView):

    def post(self, request, sale_id):
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return APIResponse.error(
                message="Sale not found.",
                status_code=404,
            )

        serializer = SaleLineSerializer(
            data=request.data
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

    def patch(self, request, sale_id, line_id):
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

        if "product" in serializer.validated_data:
            return APIResponse.error(
                message=(
                    "Use the exchange product operation "
                    "to change the product."
                ),
                status_code=400,
            )

        if "product_variant" in serializer.validated_data:
            line = SaleLineService.update_variant(
                line=line,
                product_variant=(
                    serializer.validated_data[
                        "product_variant"
                    ]
                ),
            )

        if "quantity" in serializer.validated_data:
            line = SaleLineService.update(
                line=line,
                quantity=(
                    serializer.validated_data[
                        "quantity"
                    ]
                ),
            )

        return APIResponse.success(
            data=SaleLineSerializer(line).data,
            message="Sale line updated successfully.",
        )

    def delete(self, request, sale_id, line_id):
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


class SaleLineChangeProductView(APIView):

    def post(self, request, sale_id, line_id):
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

        serializer = ChangeProductSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        replacement_lines = (
            SaleLineService.exchange_product(
                line=line,
                return_quantity=(
                    serializer.validated_data[
                        "return_quantity"
                    ]
                ),
                items=(
                    serializer.validated_data[
                        "items"
                    ]
                ),
                topup_cash_amount=(
                    serializer.validated_data.get(
                        "cash_amount"
                    )
                ),
                topup_momo_amount=(
                    serializer.validated_data.get(
                        "momo_amount"
                    )
                ),
            )
        )

        return APIResponse.success(
            data=SaleLineSerializer(
                replacement_lines,
                many=True,
            ).data,
            message=(
                "Sale line exchanged successfully."
            ),
        )


class SaleLineReturnView(APIView):

    def post(self, request, sale_id, line_id):
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

        serializer = ReturnSaleLineSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )

        SaleLineService.return_line(
            line=line,
            return_quantity=(
                serializer.validated_data[
                    "quantity"
                ]
            ),
        )

        return APIResponse.success(
            message="Sale line returned successfully.",
        )