from django.db import models

from apps.core.models import BaseModel


class Seller(BaseModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )
    class Meta:
        db_table = "sellers"
        ordering = ["name"]

    def __str__(self):
        return self.name