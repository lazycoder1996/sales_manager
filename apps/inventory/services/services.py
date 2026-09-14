from decimal import Decimal

from django.db.models import Sum

from apps.inventory.models import (
    Sale,
    SaleLine,
    Payment,
    Seller,
    SellerPayment,
    StockReceiptLine,
)


class DashboardService:

    @staticmethod
    def get_sales_summary():
        sales = Sale.objects.all()

        count = sales.count()

        total_value = (
            SaleLine.objects
            .aggregate(
                total=Sum(
                    "quantity",
                    default=Decimal("0"),
                )
            )
        )

        # Calculate from lines because the Sale model
        # intentionally does not store a total.
        total_value = sum(
            (
                line.quantity * line.unit_price
                for line in SaleLine.objects.all()
            ),
            Decimal("0"),
        )

        return {
            "count": count,
            "total_value": total_value,
        }

    @staticmethod
    def get_payment_summary():
        total_paid = (
            Payment.objects
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        total_sales = sum(
            (
                line.quantity * line.unit_price
                for line in SaleLine.objects.all()
            ),
            Decimal("0"),
        )

        outstanding = (
            total_sales - total_paid
        )

        if outstanding < 0:
            outstanding = Decimal("0")

        return {
            "total_paid": total_paid,
            "outstanding": outstanding,
        }

    @staticmethod
    def get_delivery_summary():
        sales = list(
            Sale.objects.prefetch_related(
                "lines",
                "payments",
            )
        )

        awaiting_delivery = 0
        partially_delivered = 0

        for sale in sales:
            lines = list(sale.lines.all())

            if not lines:
                continue

            total_quantity = sum(
                line.quantity
                for line in lines
            )

            delivered_quantity = sum(
                line.delivered_quantity
                for line in lines
            )

            paid_amount = sum(
                payment.amount
                for payment in sale.payments.all()
            )

            sale_total = sum(
                (
                    line.quantity * line.unit_price
                    for line in lines
                ),
                Decimal("0"),
            )

            if (
                paid_amount == sale_total
                and delivered_quantity == 0
            ):
                awaiting_delivery += 1

            elif (
                delivered_quantity > 0
                and delivered_quantity < total_quantity
            ):
                partially_delivered += 1

        return {
            "awaiting_delivery": awaiting_delivery,
            "partially_delivered": partially_delivered,
        }

    @staticmethod
    def get_stock_summary():
        received_lines = (
            StockReceiptLine.objects
            .values(
                "product",
                "product__name",
                "product_variant",
                "product_variant__size",
            )
            .annotate(
                received=Sum("quantity"),
            )
            .order_by(
                "product__name",
                "product_variant__size",
            )
        )

        delivered_lines = (
            SaleLine.objects
            .filter(
                delivered_quantity__gt=0,
            )
            .values(
                "product",
                "product_variant",
            )
            .annotate(
                delivered=Sum(
                    "delivered_quantity"
                ),
            )
        )

        delivered_map = {
            (
                item["product"],
                item["product_variant"],
            ): item["delivered"]
            for item in delivered_lines
        }

        stock = []

        for item in received_lines:
            key = (
                item["product"],
                item["product_variant"],
            )

            delivered = (
                delivered_map.get(key, 0)
            )

            received = item["received"]

            stock.append({
                "product_id": item["product"],
                "product": item["product__name"],
                "variant_id": item[
                    "product_variant"
                ],
                "variant": item[
                    "product_variant__size"
                ],
                "received": received,
                "delivered": delivered,
                "available": (
                    received - delivered
                ),
            })

        return stock

    @staticmethod
    def get_seller_summary():
        sellers = Seller.objects.all()

        seller_rows = []

        total_owed = Decimal("0")
        total_paid = Decimal("0")

        for seller in sellers:
            receipts = seller.stock_receipts.all()

            seller_owed = Decimal("0")

            for receipt in receipts:
                lines = receipt.lines.all()

                seller_owed += sum(
                    (
                        line.quantity
                        * line.unit_cost
                        for line in lines
                    ),
                    Decimal("0"),
                )

            seller_paid = (
                SellerPayment.objects
                .filter(
                    seller=seller,
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0")
            )

            seller_outstanding = (
                seller_owed - seller_paid
            )

            if seller_outstanding < 0:
                seller_outstanding = Decimal("0")

            total_owed += seller_owed
            total_paid += seller_paid

            seller_rows.append({
                "seller_id": seller.id,
                "seller": seller.name,
                "total_owed": seller_owed,
                "total_paid": seller_paid,
                "outstanding": seller_outstanding,
            })

        return {
            "total_owed": total_owed,
            "total_paid": total_paid,
            "outstanding": max(
                total_owed - total_paid,
                Decimal("0"),
            ),
            "sellers": seller_rows,
        }

    @staticmethod
    def get_earnings_summary():
        delivered_lines = (
            SaleLine.objects
            .filter(
                delivered_quantity__gt=0,
            )
            .select_related(
                "product",
                "product_variant",
            )
        )

        product_data = {}

        total_revenue = Decimal("0")
        total_cost = Decimal("0")

        for line in delivered_lines:
            delivered = line.delivered_quantity

            revenue = (
                delivered
                * line.unit_price
            )

            cost = (
                delivered
                * line.unit_cost
            )

            earnings = revenue - cost

            key = (
                line.product_id,
                line.product_variant_id,
            )

            if key not in product_data:
                product_data[key] = {
                    "product_id": line.product_id,
                    "product": line.product.name,
                    "variant_id": (
                        line.product_variant_id
                    ),
                    "variant": (
                        line.product_variant.size
                        if line.product_variant
                        else None
                    ),
                    "delivered": 0,
                    "revenue": Decimal("0"),
                    "cost": Decimal("0"),
                    "earnings": Decimal("0"),
                }

            product_data[key]["delivered"] += delivered
            product_data[key]["revenue"] += revenue
            product_data[key]["cost"] += cost
            product_data[key]["earnings"] += earnings

            total_revenue += revenue
            total_cost += cost

        return {
            "revenue": total_revenue,
            "cost": total_cost,
            "earnings": (
                total_revenue - total_cost
            ),
            "products": list(
                product_data.values()
            ),
        }

    @staticmethod
    def get_dashboard():
        return {
            "sales": (
                DashboardService
                .get_sales_summary()
            ),
            "payments": (
                DashboardService
                .get_payment_summary()
            ),
            "delivery": (
                DashboardService
                .get_delivery_summary()
            ),
            "stock": (
                DashboardService
                .get_stock_summary()
            ),
            "sellers": (
                DashboardService
                .get_seller_summary()
            ),
            "earnings": (
                DashboardService
                .get_earnings_summary()
            ),
        }