from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import SaleLine
from apps.inventory.services.stock_allocation import (
    StockAllocationService,
)


class Command(BaseCommand):
    help = (
        "Backfill FIFO stock allocations for existing sale lines."
    )

    def handle(self, *args, **options):
        sale_lines = (
            SaleLine.objects
            .select_related("sale", "product", "product_variant")
            .order_by(
                "sale__sold_at",
                "sale__created_at",
                "created_at",
            )
        )

        total_lines = sale_lines.count()
        allocated_lines = 0
        unallocated_lines = 0
        total_allocated_quantity = 0
        total_unallocated_quantity = 0

        self.stdout.write(
            self.style.WARNING(
                f"Found {total_lines} existing sale lines."
            )
        )

        for index, sale_line in enumerate(
            sale_lines.iterator(),
            start=1,
        ):
            with transaction.atomic():
                before = (
                    StockAllocationService
                    .get_sale_line_allocated_quantity(
                        sale_line,
                    )
                )

                StockAllocationService.allocate_sale_line(
                    sale_line,
                )

                after = (
                    StockAllocationService
                    .get_sale_line_allocated_quantity(
                        sale_line,
                    )
                )

                newly_allocated = after - before

                unallocated = max(
                    sale_line.quantity - after,
                    0,
                )

                if newly_allocated > 0:
                    allocated_lines += 1
                    total_allocated_quantity += newly_allocated

                if unallocated > 0:
                    unallocated_lines += 1
                    total_unallocated_quantity += unallocated

            if index % 100 == 0:
                self.stdout.write(
                    f"Processed {index}/{total_lines} sale lines..."
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "FIFO allocation backfill completed."
            )
        )

        self.stdout.write(
            f"Sale lines processed: {total_lines}"
        )

        self.stdout.write(
            f"Sale lines receiving allocations: {allocated_lines}"
        )

        self.stdout.write(
            f"Units allocated: {total_allocated_quantity}"
        )

        self.stdout.write(
            f"Sale lines still partially/fully unallocated: "
            f"{unallocated_lines}"
        )

        self.stdout.write(
            f"Units still unallocated: {total_unallocated_quantity}"
        )