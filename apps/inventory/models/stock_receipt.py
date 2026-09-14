from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models.seller import Seller


class StockReceipt(BaseModel):
    class Source(models.TextChoices):
        OWNER_SUPPLIED = "owner_supplied", "Owner supplied"
        PURCHASED_ON_BEHALF = "purchased_on_behalf", "Purchased on behalf"

    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name="stock_receipts",
    )
    source = models.CharField(
        max_length=30,
        choices=Source.choices,
    )
    received_at = models.DateTimeField()
    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "stock_receipts"
        ordering = ["-received_at", "-created_at"]

    def __str__(self):
        return f"{self.seller.name} - {self.received_at}"