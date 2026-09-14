from django.db import IntegrityError

from apps.inventory.models import ProductVariant


class ProductVariantService:
    @staticmethod
    def create(product, size):
        try:
            return ProductVariant.objects.create(
                product=product,
                size=size,
            )
        except IntegrityError:
            raise ValueError(
                "A variant with this size already exists for this product."
            )

    @staticmethod
    def update(variant, size):
        if (
            ProductVariant.objects
            .filter(
                product=variant.product,
                size=size,
            )
            .exclude(id=variant.id)
            .exists()
        ):
            raise ValueError(
                "A variant with this size already exists for this product."
            )

        variant.size = size
        variant.save(update_fields=["size", "updated_at"])
        return variant

    @staticmethod
    def activate(variant):
        if variant.is_active:
            return variant

        variant.is_active = True
        variant.save(update_fields=["is_active", "updated_at"])
        return variant

    @staticmethod
    def deactivate(variant):
        if not variant.is_active:
            return variant

        variant.is_active = False
        variant.save(update_fields=["is_active", "updated_at"])
        return variant