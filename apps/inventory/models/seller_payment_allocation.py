from django.db import models

from apps.core.models import BaseModel
from apps.inventory.models.seller_payment import SellerPayment
from apps.inventory.models.stock_receipt import StockReceipt


class SellerPaymentAllocation(BaseModel):
    seller_payment = models.ForeignKey(
        SellerPayment,
        on_delete=models.CASCADE,
        related_name="allocations",
    )

    stock_receipt = models.ForeignKey(
        StockReceipt,
        on_delete=models.PROTECT,
        related_name="payment_allocations",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        db_table = "seller_payment_allocations"
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.seller_payment} - "
            f"{self.stock_receipt}"
        )