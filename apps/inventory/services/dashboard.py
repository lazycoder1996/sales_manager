from decimal import Decimal

from django.db.models import Sum

from apps.inventory.models import (
    Payment,
    Sale,
    SaleLine,
    Seller,
    StockReceiptLine,
)
from apps.inventory.services.sale import SaleService
from apps.inventory.services.seller_payment import (
    SellerPaymentService,
)


class DashboardService:

    @staticmethod
    def get_sales_summary():
        sales = Sale.objects.all()

        total_value = Decimal("0")

        for sale in sales:
            total_value += SaleService.get_total(sale)

        return {
            "count": sales.count(),
            "total_value": total_value,
        }

    @staticmethod
    def get_payment_summary():
        total_paid = (
            Payment.objects.aggregate(
                total=Sum("amount"),
            )["total"]
            or Decimal("0")
        )

        outstanding = Decimal("0")

        for sale in Sale.objects.all():
            outstanding += SaleService.get_outstanding_amount(
                sale,
            )

        return {
            "total_paid": total_paid,
            "outstanding": outstanding,
        }

    @staticmethod
    def get_delivery_summary():
        awaiting_delivery = 0
        partially_delivered = 0

        for sale in Sale.objects.all():
            if SaleService.get_payment_status(sale) != "paid":
                continue

            delivery_status = SaleService.get_delivery_status(
                sale,
            )

            if delivery_status == "undelivered":
                awaiting_delivery += 1

            elif delivery_status == "partially_delivered":
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
                delivered=Sum("delivered_quantity"),
            )
        )

        delivered_map = {
            (
                line["product"],
                line["product_variant"],
            ): line["delivered"]
            for line in delivered_lines
        }

        stock = []

        for line in received_lines:
            key = (
                line["product"],
                line["product_variant"],
            )

            received = line["received"]
            delivered = delivered_map.get(key, 0)

            stock.append({
                "product_id": line["product"],
                "product": line["product__name"],
                "variant_id": line["product_variant"],
                "variant": line["product_variant__size"],
                "received": received,
                "delivered": delivered,
                "available": received - delivered,
            })

        return stock

    @staticmethod
    def get_seller_summary():
        sellers = Seller.objects.all()

        total_owed = Decimal("0")
        total_paid = Decimal("0")

        seller_data = []

        for seller in sellers:
            owed = SellerPaymentService.get_seller_total_owed(
                seller,
            )

            paid = SellerPaymentService.get_seller_total_paid(
                seller,
            )

            outstanding = max(
                owed - paid,
                Decimal("0"),
            )

            total_owed += owed
            total_paid += paid

            seller_data.append({
                "seller_id": seller.id,
                "seller": seller.name,
                "total_owed": owed,
                "total_paid": paid,
                "outstanding": outstanding,
            })

        return {
            "total_owed": total_owed,
            "total_paid": total_paid,
            "outstanding": max(
                total_owed - total_paid,
                Decimal("0"),
            ),
            "sellers": seller_data,
        }

    @staticmethod
    def get_earnings_summary():
        """
        Earnings are calculated from every sale line.

        Revenue:
            quantity × unit_price

        Cost:
            quantity × unit_cost

        Earnings:
            revenue − cost

        Delivery status does not affect earnings.
        """

        revenue = Decimal("0")
        cost = Decimal("0")

        product_data = {}

        sale_lines = (
            SaleLine.objects
            .select_related(
                "product",
                "product_variant",
            )
            .all()
        )

        for line in sale_lines:
            quantity = line.quantity

            line_revenue = quantity * line.unit_price
            line_cost = quantity * line.unit_cost
            line_earnings = line_revenue - line_cost

            revenue += line_revenue
            cost += line_cost

            key = (
                line.product_id,
                line.product_variant_id,
            )

            if key not in product_data:
                product_data[key] = {
                    "product_id": line.product_id,
                    "product": line.product.name,
                    "variant_id": line.product_variant_id,
                    "variant": (
                        line.product_variant.size
                        if line.product_variant
                        else None
                    ),
                    "quantity": 0,
                    "revenue": Decimal("0"),
                    "cost": Decimal("0"),
                    "earnings": Decimal("0"),
                }

            product_data[key]["quantity"] += quantity
            product_data[key]["revenue"] += line_revenue
            product_data[key]["cost"] += line_cost
            product_data[key]["earnings"] += line_earnings

        return {
            "revenue": revenue,
            "cost": cost,
            "earnings": revenue - cost,
            "products": list(product_data.values()),
        }

    @staticmethod
    def get_dashboard():
        return {
            "sales": DashboardService.get_sales_summary(),
            "payments": DashboardService.get_payment_summary(),
            "delivery": DashboardService.get_delivery_summary(),
            "stock": DashboardService.get_stock_summary(),
            "sellers": DashboardService.get_seller_summary(),
            "earnings": DashboardService.get_earnings_summary(),
        }