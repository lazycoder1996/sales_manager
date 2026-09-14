from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Seller
from apps.inventory.serializers.seller import SellerSerializer
from apps.inventory.services.seller import SellerService


class SellerListCreateView(APIView):

    def get(self, request):
        sellers = Seller.objects.all()

        is_active = request.query_params.get("is_active")

        if is_active is not None:
            is_active = is_active.lower()

            if is_active == "true":
                sellers = sellers.filter(is_active=True)
            elif is_active == "false":
                sellers = sellers.filter(is_active=False)

        return APIResponse.success(
            data=SellerSerializer(
                sellers,
                many=True,
            ).data,
            message="Sellers retrieved successfully.",
        )

    def post(self, request):
        serializer = SellerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        seller = SellerService.create(
            name=serializer.validated_data["name"],
            phone=serializer.validated_data.get("phone", ""),
            notes=serializer.validated_data.get("notes", ""),
        )

        return APIResponse.success(
            data=SellerSerializer(seller).data,
            message="Seller created successfully.",
            status_code=201,
        )


class SellerDetailView(APIView):

    def get(self, request, seller_id):
        try:
            seller = Seller.objects.get(id=seller_id)
        except Seller.DoesNotExist:
            return APIResponse.error(
                message="Seller not found.",
                status_code=404,
            )

        return APIResponse.success(
            data=SellerSerializer(seller).data,
            message="Seller retrieved successfully.",
        )

    def patch(self, request, seller_id):
        try:
            seller = Seller.objects.get(id=seller_id)
        except Seller.DoesNotExist:
            return APIResponse.error(
                message="Seller not found.",
                status_code=404,
            )

        serializer = SellerSerializer(
            seller,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        seller = SellerService.update(
            seller=seller,
            name=serializer.validated_data.get("name"),
            phone=serializer.validated_data.get("phone"),
            notes=serializer.validated_data.get("notes"),
            is_active=serializer.validated_data.get("is_active"),
        )

        return APIResponse.success(
            data=SellerSerializer(seller).data,
            message="Seller updated successfully.",
        )