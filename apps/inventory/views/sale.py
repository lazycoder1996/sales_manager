from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Sale
from apps.inventory.serializers.complete_sale import CompleteSaleSerializer
from apps.inventory.serializers.sale import SaleSerializer
from apps.inventory.services.sale import SaleService


class SaleListCreateView(APIView):

    def get(self, request):
        sales = (
            Sale.objects
            .prefetch_related(
                "lines",
                "lines__product",
                "lines__product_variant",
            )
        )

        student_number = request.query_params.get(
            "student_number"
        )

        student_name = request.query_params.get(
            "student_name"
        )

        payment_status = request.query_params.get(
            "payment_status"
        )

        delivery_status = request.query_params.get(
            "delivery_status"
        )

        if student_number:
            sales = sales.filter(
                student_number__iexact=student_number
            )

        if student_name:
            sales = sales.filter(
                student_name__icontains=student_name
            )

        sales = list(sales)

        if payment_status:
            sales = [
                sale
                for sale in sales
                if SaleService.get_payment_status(sale)
                == payment_status
            ]

        if delivery_status:
            sales = [
                sale
                for sale in sales
                if SaleService.get_delivery_status(sale)
                == delivery_status
            ]

        if student_number:
            if not sales:
                return APIResponse.error(
                    message="Sale not found.",
                    status_code=404,
                )

            return APIResponse.success(
                data=SaleSerializer(
                    sales[0]
                ).data,
            )

        return APIResponse.success(
            data=SaleSerializer(
                sales,
                many=True,
            ).data,
        )

    def post(self, request):
        serializer = SaleSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        sale = SaleService.create(
            student_number=serializer.validated_data[
                "student_number"
            ],
            student_name=serializer.validated_data[
                "student_name"
            ],
            sold_at=serializer.validated_data[
                "sold_at"
            ],
            notes=serializer.validated_data.get(
                "notes",
                "",
            ),
        )

        return APIResponse.success(
            data=SaleSerializer(sale).data,
            message="Sale created successfully.",
            status_code=201,
        )


class SaleDetailView(APIView):

    def get(self, request, sale_id):
        try:
            sale = (
                Sale.objects
                .prefetch_related(
                    "lines",
                    "lines__product",
                    "lines__product_variant",
                )
                .get(id=sale_id)
            )
        except Sale.DoesNotExist:
            return APIResponse.error(
                message="Sale not found.",
                status_code=404,
            )

        return APIResponse.success(
            data=SaleSerializer(sale).data,
        )

    def patch(self, request, sale_id):
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return APIResponse.error(
                message="Sale not found.",
                status_code=404,
            )

        serializer = SaleSerializer(
            sale,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        sale = SaleService.update(
            sale=sale,
            student_name=serializer.validated_data.get(
                "student_name"
            ),
            sold_at=serializer.validated_data.get(
                "sold_at"
            ),
            notes=serializer.validated_data.get(
                "notes"
            ),
        )

        return APIResponse.success(
            data=SaleSerializer(sale).data,
            message="Sale updated successfully.",
        )

class CompleteSaleView(APIView):

    def post(self, request):
        serializer = CompleteSaleSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        sale = SaleService.create_with_payment(
            student_number=serializer.validated_data[
                "student_number"
            ],
            student_name=serializer.validated_data[
                "student_name"
            ],
            sold_at=serializer.validated_data[
                "sold_at"
            ],
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
            notes=serializer.validated_data.get(
                "notes",
                "",
            ),
        )

        return APIResponse.success(
            data=SaleSerializer(sale).data,
            message=(
                "Sale and payment recorded "
                "successfully."
            ),
            status_code=201,
        )