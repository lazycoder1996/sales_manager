from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Payment
from apps.inventory.serializers.payment import (
    PaymentSerializer,
)
from apps.inventory.services.payment import (
    PaymentService,
)


class PaymentListCreateView(APIView):

    def get(self, request):
        payments = (
            Payment.objects
            .select_related("sale")
        )

        sale_id = request.query_params.get(
            "sale"
        )

        if sale_id:
            payments = payments.filter(
                sale_id=sale_id
            )

        return APIResponse.success(
            data=PaymentSerializer(
                payments,
                many=True,
            ).data,
        )

    def post(self, request):
        serializer = PaymentSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        payment = PaymentService.create(
            sale=serializer.validated_data[
                "sale"
            ],
            cash_amount=serializer.validated_data.get(
                "cash_amount",
                0,
            ),
            momo_amount=serializer.validated_data.get(
                "momo_amount",
                0,
            ),
            paid_at=serializer.validated_data[
                "paid_at"
            ],
        )

        return APIResponse.success(
            data=PaymentSerializer(payment).data,
            message="Payment recorded successfully.",
            status_code=201,
        )


class PaymentDetailView(APIView):

    def get(self, request, payment_id):
        try:
            payment = (
                Payment.objects
                .select_related("sale")
                .get(id=payment_id)
            )
        except Payment.DoesNotExist:
            return APIResponse.error(
                message="Payment not found.",
                status_code=404,
            )

        return APIResponse.success(
            data=PaymentSerializer(payment).data,
        )