from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.models import StockReceipt
from apps.inventory.serializers import StockReceiptSerializer
from apps.inventory.services import StockReceiptService


class StockReceiptListCreateView(APIView):

    def get(self, request):
        receipts = StockReceipt.objects.prefetch_related(
            "lines__product",
            "lines__product_variant",
        ).all()

        serializer = StockReceiptSerializer(
            receipts,
            many=True,
        )

        return APIResponse.success(
            data=serializer.data,
            message="Stock receipts retrieved successfully.",
        )

    def post(self, request):
        serializer = StockReceiptSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        receipt = StockReceiptService.create(
            seller=serializer.validated_data["seller"],
            source=serializer.validated_data["source"],
            received_at=serializer.validated_data["received_at"],
            notes=serializer.validated_data.get("notes", ""),
            lines=serializer.validated_data.get("lines", []),
        )

        receipt = StockReceipt.objects.prefetch_related(
            "lines__product",
            "lines__product_variant",
        ).get(
            id=receipt.id,
        )

        return APIResponse.success(
            data=StockReceiptSerializer(receipt).data,
            message="Stock receipt created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class StockReceiptDetailView(APIView):

    def get_object(self, receipt_id):
        return get_object_or_404(
            StockReceipt.objects.prefetch_related(
                "lines__product",
                "lines__product_variant",
            ),
            id=receipt_id,
        )

    def get(self, request, receipt_id):
        receipt = self.get_object(receipt_id)

        return APIResponse.success(
            data=StockReceiptSerializer(receipt).data,
            message="Stock receipt retrieved successfully.",
        )

    def patch(self, request, receipt_id):
        receipt = self.get_object(receipt_id)

        serializer = StockReceiptSerializer(
            receipt,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        validated_data = serializer.validated_data

        receipt = StockReceiptService.update(
            receipt=receipt,
            seller=validated_data.get("seller"),
            source=validated_data.get("source"),
            received_at=validated_data.get("received_at"),
            notes=validated_data.get("notes"),
            lines=validated_data.get("lines"),
        )

        receipt = StockReceipt.objects.prefetch_related(
            "lines__product",
            "lines__product_variant",
        ).get(
            id=receipt.id,
        )

        return APIResponse.success(
            data=StockReceiptSerializer(receipt).data,
            message="Stock receipt updated successfully.",
        )