from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models import Product, ProductVariant


class StockReceiptLine(BaseModel):
    stock_receipt = models.ForeignKey(
        "inventory.StockReceipt",
        on_delete=models.CASCADE,
        related_name="lines",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_receipt_lines",
    )

    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="stock_receipt_lines",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        db_table = "stock_receipt_lines"
        ordering = ["created_at"]

    def __str__(self):
        if self.product_variant:
            return f"{self.product_variant} - {self.quantity}"

        return f"{self.product} - {self.quantity}"