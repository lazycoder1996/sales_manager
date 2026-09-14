from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models.seller import Seller


class SellerPayment(BaseModel):
    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    paid_at = models.DateTimeField()

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "seller_payments"
        ordering = ["-paid_at", "-created_at"]

    def __str__(self):
        return (
            f"{self.seller.name} - "
            f"GHS {self.amount}"
        )