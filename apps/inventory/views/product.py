from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Product
from apps.inventory.serializers import ProductSerializer
from apps.inventory.services import ProductService


class ProductListCreateView(APIView):

    def get(self, request):
        products = Product.objects.all()

        serializer = ProductSerializer(
            products,
            many=True,
        )

        return APIResponse.success(
            data=serializer.data,
            message="Products retrieved successfully.",
        )

    def post(self, request):
        serializer = ProductSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        product = ProductService.create(
            name=serializer.validated_data["name"],
            cost_price=serializer.validated_data["cost_price"],
            selling_price=serializer.validated_data["selling_price"],
            required=serializer.validated_data.get(
                "required",
                True,
            ),
            required_quantity=serializer.validated_data.get(
                "required_quantity",
                1,
            ),
        )

        return APIResponse.success(
            data=ProductSerializer(product).data,
            message="Product created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ProductDetailView(APIView):

    def get_object(self, product_id):
        return get_object_or_404(
            Product,
            id=product_id,
        )

    def get(self, request, product_id):
        product = self.get_object(product_id)

        return APIResponse.success(
            data=ProductSerializer(product).data,
            message="Product retrieved successfully.",
        )

    def patch(self, request, product_id):
        product = self.get_object(product_id)

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        product = ProductService.update(
            product=product,
            name=serializer.validated_data.get(
                "name"
            ),
            cost_price=serializer.validated_data.get(
                "cost_price"
            ),
            selling_price=serializer.validated_data.get(
                "selling_price"
            ),
            required=serializer.validated_data.get(
                "required"
            ),
            required_quantity=serializer.validated_data.get(
                "required_quantity"
            ),
        )

        return APIResponse.success(
            data=ProductSerializer(product).data,
            message="Product updated successfully.",
        )


class ProductActivateView(APIView):

    def post(self, request, product_id):
        product = get_object_or_404(
            Product,
            id=product_id,
        )

        product = ProductService.activate(
            product
        )

        return APIResponse.success(
            data=ProductSerializer(product).data,
            message="Product activated successfully.",
        )


class ProductDeactivateView(APIView):

    def post(self, request, product_id):
        product = get_object_or_404(
            Product,
            id=product_id,
        )

        product = ProductService.deactivate(
            product
        )

        return APIResponse.success(
            data=ProductSerializer(product).data,
            message="Product deactivated successfully.",
        )