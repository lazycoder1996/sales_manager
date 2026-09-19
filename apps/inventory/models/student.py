from django.db import models

from apps.core.models.base import BaseModel


class Student(BaseModel):
    admission_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    firstname = models.CharField(
        max_length=100,
    )

    middlename = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    surname = models.CharField(
        max_length=100,
    )

    fathers_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    fathers_contact = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    mothers_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    mothers_contact = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    residence = models.CharField(
        max_length=255,
        null=True
    )

    date_of_birth = models.DateField(
        null=True
    )
    is_active = models.BooleanField(
        default=True
    )

    house = models.ForeignKey(
        "inventory.House",
        on_delete=models.PROTECT,
        related_name="students",
        null=True
    )

    class Meta:
        db_table = "students"
        ordering = [
            "surname",
            "firstname",
            "created_at",
        ]

    def __str__(self):
        name_parts = [
            self.firstname,
            self.middlename,
            self.surname,
        ]

        full_name = " ".join(
            part
            for part in name_parts
            if part
        )

        return (
            self.admission_number
            or full_name
            or str(self.id)
        )