from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.inventory.models import SaleLine
from apps.inventory.services.stock_allocation import (
    StockAllocationService,
)


class SaleLineService:

    @staticmethod
    def _get_payment_for_adjustment(sale):
        payment = (
            sale.payments
            .select_for_update()
            .order_by("-paid_at", "-created_at")
            .first()
        )

        if payment is None:
            raise serializers.ValidationError(
                "No payment exists for this sale."
            )

        return payment

    @staticmethod
    def _adjust_payment(
        sale,
        difference,
        cash_amount=Decimal("0.00"),
        momo_amount=Decimal("0.00"),
    ):
        payment = SaleLineService._get_payment_for_adjustment(
            sale
        )

        if difference == 0:
            if (
                cash_amount != Decimal("0.00")
                or momo_amount != Decimal("0.00")
            ):
                raise serializers.ValidationError(
                    "No payment adjustment is required."
                )

            return payment

        # Customer is owed money.
        #
        # Refunds are always treated as cash refunds.
        # This means the refund does not depend on how the
        # original payment was split between cash and MoMo.
        if difference < 0:
            refund = abs(difference)

            payment.cash_amount -= refund
            payment.amount -= refund

            payment.save(
                update_fields=[
                    "cash_amount",
                    "amount",
                    "updated_at",
                ],
            )

            return payment

        # Customer needs to pay more.
        if (
            cash_amount < Decimal("0.00")
            or momo_amount < Decimal("0.00")
        ):
            raise serializers.ValidationError(
                "Cash and Mobile Money amounts cannot be negative."
            )

        if (
            cash_amount + momo_amount
            != difference
        ):
            raise serializers.ValidationError(
                "Cash and Mobile Money amounts must exactly equal "
                "the required payment adjustment."
            )

        payment.cash_amount += cash_amount
        payment.momo_amount += momo_amount
        payment.amount += difference

        payment.save(
            update_fields=[
                "cash_amount",
                "momo_amount",
                "amount",
                "updated_at",
            ],
        )

        return payment

    @staticmethod
    def _validate_product_variant(
        product,
        product_variant,
    ):
        active_variants = product.variants.filter(
            is_active=True,
        )

        if (
            active_variants.exists()
            and product_variant is None
        ):
            raise serializers.ValidationError(
                "A variant is required for this product."
            )

        if (
            not active_variants.exists()
            and product_variant is not None
        ):
            raise serializers.ValidationError(
                "This product does not have variants."
            )

        if product_variant is not None:
            if product_variant.product_id != product.id:
                raise serializers.ValidationError(
                    "The selected variant does not belong to "
                    "the selected product."
                )

            if not product_variant.is_active:
                raise serializers.ValidationError(
                    "Product variant is inactive."
                )

    @staticmethod
    @transaction.atomic
    def create(
        sale,
        product,
        product_variant,
        quantity,
    ):
        SaleLineService._validate_product_variant(
            product,
            product_variant,
        )

        existing_line = (
            SaleLine.objects
            .select_for_update()
            .filter(
                sale=sale,
                product=product,
                product_variant=product_variant,
            )
            .first()
        )

        if existing_line:
            existing_line.quantity += quantity

            existing_line.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ],
            )

            StockAllocationService.allocate_sale_line(
                existing_line,
            )

            return existing_line

        line = SaleLine.objects.create(
            sale=sale,
            product=product,
            product_variant=product_variant,
            quantity=quantity,
            delivered_quantity=0,
            unit_price=product.selling_price,
            unit_cost=product.cost_price,
        )

        StockAllocationService.allocate_sale_line(
            line
        )

        return line

    @staticmethod
    @transaction.atomic
    def update(
        line,
        quantity,
    ):
        locked_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        if quantity < 1:
            raise serializers.ValidationError(
                "Quantity must be at least 1."
            )

        if quantity < locked_line.delivered_quantity:
            raise serializers.ValidationError(
                "Quantity cannot be less than the delivered quantity."
            )

        old_quantity = locked_line.quantity

        if quantity == old_quantity:
            return locked_line

        difference_quantity = (
            quantity - old_quantity
        )

        if difference_quantity > 0:
            difference = (
                Decimal(difference_quantity)
                * locked_line.unit_price
            )

            SaleLineService._adjust_payment(
                sale=locked_line.sale,
                difference=difference,
            )

            locked_line.quantity = quantity

            locked_line.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ],
            )

            StockAllocationService.allocate_sale_line(
                locked_line,
            )

            return locked_line

        reduction_quantity = abs(
            difference_quantity
        )

        difference = (
            Decimal(reduction_quantity)
            * locked_line.unit_price
        )

        SaleLineService._adjust_payment(
            sale=locked_line.sale,
            difference=-difference,
        )

        StockAllocationService.reduce_sale_line_allocations(
            sale_line=locked_line,
            quantity=reduction_quantity,
        )

        locked_line.quantity = quantity

        locked_line.save(
            update_fields=[
                "quantity",
                "updated_at",
            ],
        )

        return locked_line

    @staticmethod
    @transaction.atomic
    def update_variant(
        line,
        product_variant,
    ):
        locked_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        if locked_line.delivered_quantity > 0:
            raise serializers.ValidationError(
                "The product variant cannot be changed after delivery."
            )

        if product_variant is None:
            raise serializers.ValidationError(
                "A product variant is required."
            )

        if product_variant.product_id != locked_line.product_id:
            raise serializers.ValidationError(
                "The selected variant does not belong to this product."
            )

        if not product_variant.is_active:
            raise serializers.ValidationError(
                "Product variant is inactive."
            )

        duplicate = (
            SaleLine.objects
            .filter(
                sale=locked_line.sale,
                product=locked_line.product,
                product_variant=product_variant,
            )
            .exclude(pk=locked_line.pk)
            .exists()
        )

        if duplicate:
            raise serializers.ValidationError(
                "This product and variant already exists on the sale."
            )

        StockAllocationService.clear_sale_line_allocations(
            locked_line
        )

        locked_line.product_variant = product_variant

        locked_line.save(
            update_fields=[
                "product_variant",
                "updated_at",
            ],
        )

        StockAllocationService.allocate_sale_line(
            locked_line
        )

        return locked_line

    @staticmethod
    @transaction.atomic
    def delete(line):
        locked_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        if locked_line.delivered_quantity > 0:
            raise serializers.ValidationError(
                "A delivered sale line cannot be deleted."
            )

        refund = (
            Decimal(locked_line.quantity)
            * locked_line.unit_price
        )

        SaleLineService._adjust_payment(
            sale=locked_line.sale,
            difference=-refund,
        )

        StockAllocationService.clear_sale_line_allocations(
            locked_line
        )

        locked_line.delete()

    @staticmethod
    @transaction.atomic
    def exchange_product(
        line,
        return_quantity,
        items,
        cash_amount=Decimal("0.00"),
        momo_amount=Decimal("0.00"),
    ):
        locked_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        sale = locked_line.sale

        if return_quantity < 1:
            raise serializers.ValidationError(
                "Return quantity must be at least 1."
            )

        if return_quantity > locked_line.quantity:
            raise serializers.ValidationError(
                "Return quantity cannot exceed the purchased quantity."
            )

        if not items:
            raise serializers.ValidationError(
                "At least one replacement item is required."
            )

        returned_value = (
            Decimal(return_quantity)
            * locked_line.unit_price
        )

        replacement_total = Decimal("0.00")

        for item in items:
            product = item["product"]
            product_variant = item.get("product_variant")
            quantity = item["quantity"]

            SaleLineService._validate_product_variant(
                product,
                product_variant,
            )

            replacement_total += (
                Decimal(quantity)
                * product.selling_price
            )

        difference = (
            replacement_total
            - returned_value
        )

        SaleLineService._adjust_payment(
            sale=sale,
            difference=difference,
            cash_amount=cash_amount,
            momo_amount=momo_amount,
        )

        StockAllocationService.reduce_sale_line_allocations(
            sale_line=locked_line,
            quantity=return_quantity,
        )

        delivered_to_remove = min(
            locked_line.delivered_quantity,
            return_quantity,
        )

        locked_line.quantity -= return_quantity
        locked_line.delivered_quantity -= delivered_to_remove

        if locked_line.quantity <= 0:
            StockAllocationService.clear_sale_line_allocations(
                locked_line
            )

            locked_line.delete()
        else:
            locked_line.save(
                update_fields=[
                    "quantity",
                    "delivered_quantity",
                    "updated_at",
                ],
            )

        created_lines = []

        for item in items:
            product = item["product"]
            product_variant = item.get("product_variant")
            quantity = item["quantity"]

            replacement_line = (
                SaleLine.objects
                .select_for_update()
                .filter(
                    sale=sale,
                    product=product,
                    product_variant=product_variant,
                )
                .first()
            )

            if replacement_line:
                replacement_line.quantity += quantity

                replacement_line.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ],
                )

                StockAllocationService.allocate_sale_line(
                    replacement_line
                )

                created_lines.append(
                    replacement_line
                )

                continue

            replacement_line = SaleLine.objects.create(
                sale=sale,
                product=product,
                product_variant=product_variant,
                quantity=quantity,
                delivered_quantity=0,
                unit_price=product.selling_price,
                unit_cost=product.cost_price,
            )

            StockAllocationService.allocate_sale_line(
                replacement_line
            )

            created_lines.append(
                replacement_line
            )

        return created_lines

    @staticmethod
    @transaction.atomic
    def return_line(
        line,
        return_quantity,
    ):
        locked_line = (
            SaleLine.objects
            .select_for_update()
            .get(pk=line.pk)
        )

        if return_quantity < 1:
            raise serializers.ValidationError(
                "Return quantity must be at least 1."
            )

        if return_quantity > locked_line.quantity:
            raise serializers.ValidationError(
                "Return quantity cannot exceed the purchased quantity."
            )

        refund = (
            Decimal(return_quantity)
            * locked_line.unit_price
        )

        SaleLineService._adjust_payment(
            sale=locked_line.sale,
            difference=-refund,
        )

        StockAllocationService.reduce_sale_line_allocations(
            sale_line=locked_line,
            quantity=return_quantity,
        )

        delivered_to_remove = min(
            locked_line.delivered_quantity,
            return_quantity,
        )

        if return_quantity == locked_line.quantity:
            StockAllocationService.clear_sale_line_allocations(
                locked_line
            )

            locked_line.delete()

            return

        locked_line.quantity -= return_quantity
        locked_line.delivered_quantity -= delivered_to_remove

        locked_line.save(
            update_fields=[
                "quantity",
                "delivered_quantity",
                "updated_at",
            ],
        )

        return locked_line