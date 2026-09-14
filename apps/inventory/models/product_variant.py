from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models import Product

class ProductVariant(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    size = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "product_variants"
        ordering = ["size"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "size"],
                name="unique_product_variant_size",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size}"