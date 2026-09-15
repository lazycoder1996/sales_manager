from django.db.models import Q
from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.core.responses.pagination import CursorPagination
from apps.inventory.models import Sale
from apps.inventory.serializers.complete_sale import CompleteSaleSerializer
from apps.inventory.serializers.sale import SaleSerializer
from apps.inventory.services.sale import SaleService
from datetime import datetime, time
from django.utils import timezone

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

        search = request.query_params.get("search")

        if search:
            sales = sales.filter(
                Q(student_number__iexact=search)
                | Q(student_name__icontains=search)
            )
        date_value = request.query_params.get("date")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_value:
            try:
                selected_date = datetime.strptime(
                    date_value,
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                return APIResponse.error(
                    message="Invalid date. Use YYYY-MM-DD.",
                    status_code=400,
                )

            sales = sales.filter(
                sold_at__date=selected_date,
            )

        else:
            if date_from:
                try:
                    start_date = datetime.strptime(
                        date_from,
                        "%Y-%m-%d",
                    ).date()
                except ValueError:
                    return APIResponse.error(
                        message="Invalid date_from. Use YYYY-MM-DD.",
                        status_code=400,
                    )

                sales = sales.filter(
                    sold_at__date__gte=start_date,
                )

            if date_to:
                try:
                    end_date = datetime.strptime(
                        date_to,
                        "%Y-%m-%d",
                    ).date()
                except ValueError:
                    return APIResponse.error(
                        message="Invalid date_to. Use YYYY-MM-DD.",
                        status_code=400,
                    )

                sales = sales.filter(
                    sold_at__date__lte=end_date,
                )
        # student_number = request.query_params.get(
        #     "student_number"
        # )

        # student_name = request.query_params.get(
        #     "student_name"
        # )

        payment_status = request.query_params.get(
            "payment_status"
        )

        delivery_status = request.query_params.get(
            "delivery_status"
        )

        # if student_number:
        #     sales = sales.filter(
        #         student_number__iexact=student_number
        #     )

        # if student_name:
        #     sales = sales.filter(
        #         student_name__icontains=student_name
        #     )

        # sales = list(sales)

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

        # if student_number:
        #     if not sales:
        #         return APIResponse.error(
        #             message="Sale not found.",
        #             status_code=404,
        #         )

        #     return APIResponse.success(
        #         data=SaleSerializer(
        #             sales[0]
        #         ).data,
        #     )
        data = CursorPagination.paginate(
            queryset=sales,
            request=request,
            serializer_class=SaleSerializer,
            ordering="-sold_at",
        )

        return APIResponse.success(data=data)

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