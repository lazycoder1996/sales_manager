from django.db import models

from apps.core.models.base import BaseModel



class House(BaseModel):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    name = models.CharField(
        max_length=100,
    )

    code = models.CharField(
        max_length=20,
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
    )

    color = models.CharField(
        max_length=7,
    )

    partner_house = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partner",
    )

    class Meta:
        db_table = "houses"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "gender",
                ],
                name="unique_house_name_gender",
            ),
            models.UniqueConstraint(
                fields=[
                    "code",
                    "gender",
                ],
                name="unique_house_code_gender",
            ),
        ]

    def __str__(self):
        return self.name