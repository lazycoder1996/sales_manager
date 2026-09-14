from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import Product, ProductVariant
from apps.inventory.serializers import ProductVariantSerializer
from apps.inventory.services import ProductVariantService


class ProductVariantListCreateView(APIView):
    def get_product(self, product_id):
        return get_object_or_404(
            Product,
            id=product_id,
        )

    def get(self, request, product_id):
        product = self.get_product(product_id)

        variants = product.variants.all()
        serializer = ProductVariantSerializer(
            variants,
            many=True,
        )

        return APIResponse.success(
            data=serializer.data,
            message="Product variants retrieved successfully.",
        )

    def post(self, request, product_id):
        product = self.get_product(product_id)

        serializer = ProductVariantSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            variant = ProductVariantService.create(
                product=product,
                size=serializer.validated_data["size"],
            )
        except ValueError as exc:
            return APIResponse.error(
                error=str(exc),
                message="Unable to create product variant.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return APIResponse.success(
            data=ProductVariantSerializer(variant).data,
            message="Product variant created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ProductVariantDetailView(APIView):
    def get_object(self, product_id, variant_id):
        return get_object_or_404(
            ProductVariant,
            id=variant_id,
            product_id=product_id,
        )

    def get(self, request, product_id, variant_id):
        variant = self.get_object(
            product_id,
            variant_id,
        )

        return APIResponse.success(
            data=ProductVariantSerializer(variant).data,
            message="Product variant retrieved successfully.",
        )

    def patch(self, request, product_id, variant_id):
        variant = self.get_object(
            product_id,
            variant_id,
        )

        serializer = ProductVariantSerializer(
            variant,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            variant = ProductVariantService.update(
                variant=variant,
                size=serializer.validated_data["size"],
            )
        except ValueError as exc:
            return APIResponse.error(
                error=str(exc),
                message="Unable to update product variant.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return APIResponse.success(
            data=ProductVariantSerializer(variant).data,
            message="Product variant updated successfully.",
        )


class ProductVariantActivateView(APIView):
    def post(self, request, product_id, variant_id):
        variant = get_object_or_404(
            ProductVariant,
            id=variant_id,
            product_id=product_id,
        )

        variant = ProductVariantService.activate(variant)

        return APIResponse.success(
            data=ProductVariantSerializer(variant).data,
            message="Product variant activated successfully.",
        )


class ProductVariantDeactivateView(APIView):
    def post(self, request, product_id, variant_id):
        variant = get_object_or_404(
            ProductVariant,
            id=variant_id,
            product_id=product_id,
        )

        variant = ProductVariantService.deactivate(variant)

        return APIResponse.success(
            data=ProductVariantSerializer(variant).data,
            message="Product variant deactivated successfully.",
        )