from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import Seller


class SellerService:

    @staticmethod
    @transaction.atomic
    def create(
        name,
        phone="",
        notes="",
    ):
        name = name.strip()

        if Seller.objects.filter(
            name__iexact=name,
        ).exists():
            raise serializers.ValidationError({
                "name": "A seller with this name already exists."
            })

        return Seller.objects.create(
            name=name,
            phone=phone,
            notes=notes,
        )

    @staticmethod
    @transaction.atomic
    def update(
        seller,
        name=None,
        phone=None,
        notes=None,
        is_active=None,
    ):
        if name is not None:
            name = name.strip()

            if not name:
                raise serializers.ValidationError({
                    "name": "Seller name is required."
                })

            duplicate = (
                Seller.objects
                .filter(name__iexact=name)
                .exclude(id=seller.id)
                .exists()
            )

            if duplicate:
                raise serializers.ValidationError({
                    "name": "A seller with this name already exists."
                })

            seller.name = name

        if phone is not None:
            seller.phone = phone

        if notes is not None:
            seller.notes = notes

        if is_active is not None:
            seller.is_active = is_active

        seller.save()

        return seller