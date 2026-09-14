from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import SellerPayment
from apps.inventory.serializers.seller_payment import (
    SellerPaymentSerializer,
)
from apps.inventory.services.seller_payment import (
    SellerPaymentService,
)


class SellerPaymentListCreateView(APIView):

    def get(self, request):
        payments = (
            SellerPayment.objects
            .select_related("seller")
        )

        seller_id = request.query_params.get("seller")

        if seller_id:
            payments = payments.filter(
                seller_id=seller_id,
            )

        return APIResponse.success(
            data=SellerPaymentSerializer(
                payments,
                many=True,
            ).data,
            message="Seller payments retrieved successfully.",
        )

    def post(self, request):
        serializer = SellerPaymentSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        payment = SellerPaymentService.create(
            seller=serializer.validated_data["seller"],
            amount=serializer.validated_data["amount"],
            paid_at=serializer.validated_data["paid_at"],
            notes=serializer.validated_data.get(
                "notes",
                "",
            ),
        )

        return APIResponse.success(
            data=SellerPaymentSerializer(
                payment,
            ).data,
            message="Seller payment recorded successfully.",
            status_code=201,
        )


class SellerPaymentDetailView(APIView):

    def get(self, request, payment_id):
        try:
            payment = (
                SellerPayment.objects
                .select_related("seller")
                .get(id=payment_id)
            )
        except SellerPayment.DoesNotExist:
            return APIResponse.error(
                message="Seller payment not found.",
                status_code=404,
            )

        return APIResponse.success(
            data=SellerPaymentSerializer(
                payment,
            ).data,
            message="Seller payment retrieved successfully.",
        )