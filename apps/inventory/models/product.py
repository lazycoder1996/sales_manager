from django.db import models

from apps.core.models import BaseModel


class Product(BaseModel):
    name = models.CharField(max_length=255)
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    is_active = models.BooleanField(default=True)
    required = models.BooleanField(default=True)
    required_quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "products"
        ordering = ["name"]

    def __str__(self):
        return self.name


