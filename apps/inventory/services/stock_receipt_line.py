from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Product
from apps.inventory.models import ProductVariant
from apps.inventory.models import StockReceiptLine
from apps.inventory.services.stock_allocation import (
    StockAllocationService,
)


class StockReceiptLineService:

    @staticmethod
    def _validate_product(product):
        if not product.is_active:
            raise serializers.ValidationError(
                "Product is inactive."
            )

    @staticmethod
    def _validate_product_variant(product, product_variant):
        active_variants = product.variants.filter(
            is_active=True,
        )

        if active_variants.exists() and product_variant is None:
            raise serializers.ValidationError(
                "A variant is required for this product."
            )

        if not active_variants.exists() and product_variant is not None:
            raise serializers.ValidationError(
                "This product does not have variants."
            )

        if product_variant is not None:
            if product_variant.product_id != product.id:
                raise serializers.ValidationError(
                    "The selected variant does not belong to the selected product."
                )

            if not product_variant.is_active:
                raise serializers.ValidationError(
                    "Product variant is inactive."
                )

    @staticmethod
    @transaction.atomic
    def create(
        stock_receipt,
        product,
        product_variant,
        quantity,
    ):
        StockReceiptLineService._validate_product(product)

        StockReceiptLineService._validate_product_variant(
            product,
            product_variant,
        )

        line = StockReceiptLine.objects.create(
            stock_receipt=stock_receipt,
            product=product,
            product_variant=product_variant,
            quantity=quantity,
            unit_cost=product.cost_price,
        )

        # Newly received stock can satisfy previously unallocated sales.
        StockAllocationService.allocate_receipt_line(line)

        return line

    @staticmethod
    @transaction.atomic
    def update(
        line,
        product=None,
        product_variant=None,
        quantity=None,
        update_product=False,
        update_product_variant=False,
        update_quantity=False,
    ):
        current_product = line.product
        current_variant = line.product_variant
        current_quantity = line.quantity

        final_product = (
            product
            if update_product
            else current_product
        )

        final_variant = (
            product_variant
            if update_product_variant
            else current_variant
        )

        if update_product:
            StockReceiptLineService._validate_product(
                final_product,
            )

        if update_product or update_product_variant:
            StockReceiptLineService._validate_product_variant(
                final_product,
                final_variant,
            )

        allocated_quantity = (
            StockAllocationService
            .get_receipt_line_allocated_quantity(line)
        )

        # Product/variant cannot change once any units from this
        # receipt line have been allocated to a sale.
        if (
            (update_product or update_product_variant)
            and allocated_quantity > 0
        ):
            raise serializers.ValidationError(
                "Product or variant cannot be changed because stock from "
                "this receipt line has already been allocated to a sale."
            )

        if update_quantity:
            if quantity is None or quantity < 1:
                raise serializers.ValidationError(
                    "Quantity must be greater than zero."
                )

            # Never allow the physical receipt quantity to become
            # smaller than the quantity already allocated to sales.
            if quantity < allocated_quantity:
                raise serializers.ValidationError(
                    f"Quantity cannot be reduced below {allocated_quantity} "
                    "because {allocated_quantity} unit(s) have already "
                    "been allocated to sales."
                )

        if update_product:
            line.product = final_product

            # Cost is a snapshot of the product cost when the receipt
            # line is created/changed before allocation.
            line.unit_cost = final_product.cost_price

        if update_product_variant:
            line.product_variant = final_variant

        if update_quantity:
            line.quantity = quantity

        line.save(
            update_fields=[
                "product",
                "product_variant",
                "quantity",
                "unit_cost",
                "updated_at",
            ],
        )

        # If quantity increased, the newly available stock can now
        # be allocated to the oldest unallocated sales.
        if update_quantity and quantity > current_quantity:
            StockAllocationService.allocate_receipt_line(line)

        return line

    @staticmethod
    @transaction.atomic
    def delete(line):
        allocated_quantity = (
            StockAllocationService
            .get_receipt_line_allocated_quantity(line)
        )

        if allocated_quantity > 0:
            raise serializers.ValidationError(
                "This receipt line cannot be deleted because "
                "some of its stock has already been allocated to sales."
            )

        line.delete()