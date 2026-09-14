from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models.product import Product
from apps.inventory.models.product_variant import ProductVariant
from apps.inventory.models.sale import Sale


class SaleLine(BaseModel):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sale_lines",
    )

    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="sale_lines",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    delivered_quantity = models.PositiveIntegerField(
        default=0,
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        db_table = "sale_lines"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product} - {self.quantity}"