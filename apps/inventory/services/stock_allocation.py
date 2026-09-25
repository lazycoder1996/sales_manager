from decimal import Decimal

from django.db import transaction

from apps.inventory.models import (
    SaleLine,
    SaleLineStockAllocation,
    StockReceiptLine,
)


class StockAllocationService:
    """
    Handles FIFO cost allocation between sold quantities and stock receipt
    quantities.

    Important:
    - This is NOT the physical stock/delivery system.
    - A sale can exist without any stock allocation.
    - Allocations are only used to determine the seller/cost basis of sold
      units.
    """

    @staticmethod
    def _get_allocated_quantity(stock_receipt_line):
        return (
            SaleLineStockAllocation.objects
            .filter(stock_receipt_line=stock_receipt_line)
            .aggregate_total_quantity()
        )

    @staticmethod
    def _get_allocated_quantity_for_receipt_line(stock_receipt_line):
        allocations = SaleLineStockAllocation.objects.filter(
            stock_receipt_line=stock_receipt_line,
        )

        return sum(
            allocation.quantity
            for allocation in allocations
        )

    @staticmethod
    def _get_allocated_quantity_for_sale_line(sale_line):
        allocations = SaleLineStockAllocation.objects.filter(
            sale_line=sale_line,
        )

        return sum(
            allocation.quantity
            for allocation in allocations
        )

    @staticmethod
    def get_sale_line_allocated_quantity(sale_line):
        return StockAllocationService._get_allocated_quantity_for_sale_line(
            sale_line,
        )

    @staticmethod
    def get_sale_line_unallocated_quantity(sale_line):
        allocated = (
            StockAllocationService
            .get_sale_line_allocated_quantity(sale_line)
        )

        return max(
            sale_line.quantity - allocated,
            0,
        )

    @staticmethod
    def get_sale_line_cost(sale_line):
        allocations = (
            SaleLineStockAllocation.objects
            .filter(sale_line=sale_line)
            .select_related("stock_receipt_line")
        )

        total = Decimal("0.00")

        for allocation in allocations:
            total += (
                Decimal(allocation.quantity)
                * allocation.unit_cost
            )

        return total

    @staticmethod
    @transaction.atomic
    def allocate_sale_line(sale_line):
        """
        Allocate currently unallocated sold quantity against available
        receipt stock using FIFO.

        FIFO order:
        1. receipt received_at
        2. receipt created_at
        3. receipt-line created_at
        """

        locked_sale_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=sale_line.pk)
        )

        allocated_quantity = (
            StockAllocationService
            .get_sale_line_allocated_quantity(locked_sale_line)
        )

        remaining_quantity = (
            locked_sale_line.quantity - allocated_quantity
        )

        if remaining_quantity <= 0:
            return locked_sale_line

        receipt_lines = (
            StockReceiptLine.objects
            .select_related("stock_receipt")
            .filter(
                product_id=locked_sale_line.product_id,
                product_variant_id=locked_sale_line.product_variant_id,
            )
            .order_by(
                "stock_receipt__received_at",
                "stock_receipt__created_at",
                "created_at",
            )
            .select_for_update()
        )

        for receipt_line in receipt_lines:
            if remaining_quantity <= 0:
                break

            already_allocated = (
                StockAllocationService
                ._get_allocated_quantity_for_receipt_line(
                    receipt_line,
                )
            )

            available_quantity = (
                receipt_line.quantity - already_allocated
            )

            if available_quantity <= 0:
                continue

            allocation_quantity = min(
                remaining_quantity,
                available_quantity,
            )

            SaleLineStockAllocation.objects.create(
                sale_line=locked_sale_line,
                stock_receipt_line=receipt_line,
                quantity=allocation_quantity,
                unit_cost=receipt_line.unit_cost,
            )

            remaining_quantity -= allocation_quantity

        return locked_sale_line

    @staticmethod
    @transaction.atomic
    def allocate_receipt_line(stock_receipt_line):
        """
        Allocate newly available receipt stock to the oldest unallocated
        sales for the same product/variant.

        FIFO order:
        1. sale sold_at
        2. sale created_at
        3. sale-line created_at
        """

        locked_receipt_line = (
            StockReceiptLine.objects
            .select_for_update()
            .get(pk=stock_receipt_line.pk)
        )

        already_allocated = (
            StockAllocationService
            ._get_allocated_quantity_for_receipt_line(
                locked_receipt_line,
            )
        )

        remaining_quantity = (
            locked_receipt_line.quantity - already_allocated
        )

        if remaining_quantity <= 0:
            return locked_receipt_line

        sale_lines = (
            SaleLine.objects
            .select_related("sale")
            .filter(
                product_id=locked_receipt_line.product_id,
                product_variant_id=locked_receipt_line.product_variant_id,
            )
            .order_by(
                "sale__sold_at",
                "sale__created_at",
                "created_at",
            )
            .select_for_update()
        )

        for sale_line in sale_lines:
            if remaining_quantity <= 0:
                break

            allocated_quantity = (
                StockAllocationService
                ._get_allocated_quantity_for_sale_line(
                    sale_line,
                )
            )

            unallocated_quantity = (
                sale_line.quantity - allocated_quantity
            )

            if unallocated_quantity <= 0:
                continue

            allocation_quantity = min(
                remaining_quantity,
                unallocated_quantity,
            )

            SaleLineStockAllocation.objects.create(
                sale_line=sale_line,
                stock_receipt_line=locked_receipt_line,
                quantity=allocation_quantity,
                unit_cost=locked_receipt_line.unit_cost,
            )

            remaining_quantity -= allocation_quantity

        return locked_receipt_line

    @staticmethod
    @transaction.atomic
    def reduce_sale_line_allocations(
        sale_line,
        quantity,
    ):
        """
        Remove FIFO allocations when sold quantity is reduced.

        Allocations are removed from the newest allocation first.

        It is valid for `quantity` to exceed the currently allocated
        quantity because a sale may contain units that were sold before
        sufficient stock existed.

        Returns the number of allocated units actually removed.
        """

        if quantity <= 0:
            return 0

        allocations = list(
            SaleLineStockAllocation.objects
            .select_for_update()
            .filter(sale_line=sale_line)
            .order_by(
                "-created_at",
                "-id",
            )
        )

        remaining_to_remove = quantity
        removed_quantity = 0

        for allocation in allocations:
            if remaining_to_remove <= 0:
                break

            remove_quantity = min(
                allocation.quantity,
                remaining_to_remove,
            )

            if remove_quantity == allocation.quantity:
                allocation.delete()
            else:
                allocation.quantity -= remove_quantity
                allocation.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ],
                )

            remaining_to_remove -= remove_quantity
            removed_quantity += remove_quantity

        return removed_quantity

    @staticmethod
    @transaction.atomic
    def clear_sale_line_allocations(sale_line):
        """
        Remove all FIFO allocations for a sale line.

        Used when changing the product/variant of an undelivered sale line.
        """

        SaleLineStockAllocation.objects.filter(
            sale_line=sale_line,
        ).delete()

    @staticmethod
    def get_receipt_line_allocated_quantity(stock_receipt_line):
        return (
            StockAllocationService
            ._get_allocated_quantity_for_receipt_line(
                stock_receipt_line,
            )
        )

    @staticmethod
    def get_receipt_line_unallocated_quantity(stock_receipt_line):
        allocated = (
            StockAllocationService
            .get_receipt_line_allocated_quantity(
                stock_receipt_line,
            )
        )

        return max(
            stock_receipt_line.quantity - allocated,
            0,
        )

    @staticmethod
    def get_seller_total_owed(seller):
        allocations = (
            SaleLineStockAllocation.objects
            .filter(
                stock_receipt_line__stock_receipt__seller=seller,
            )
            .only(
                "quantity",
                "unit_cost",
            )
        )

        total = Decimal("0.00")

        for allocation in allocations:
            total += (
                Decimal(allocation.quantity)
                * allocation.unit_cost
            )

        return total