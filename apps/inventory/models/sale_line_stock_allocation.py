from django.db import models
from django.core.validators import MinValueValidator

from apps.core.models import BaseModel
from apps.inventory.models.sale_line import SaleLine
from apps.inventory.models.stock_receipt_line import StockReceiptLine


class SaleLineStockAllocation(BaseModel):
    sale_line = models.ForeignKey(
        SaleLine,
        on_delete=models.PROTECT,
        related_name="stock_allocations",
    )

    stock_receipt_line = models.ForeignKey(
        StockReceiptLine,
        on_delete=models.PROTECT,
        related_name="sale_allocations",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        db_table = "sale_line_stock_allocations"
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.sale_line} - "
            f"{self.stock_receipt_line} - "
            f"{self.quantity}"
        )