from django.db.models import Prefetch

from apps.inventory.models import Sale, SaleLine


class StudentHistoryService:

    @staticmethod
    def get_by_student_number(student_number):
        return (
            Sale.objects
            .filter(
                student_number__iexact=student_number
            )
            .prefetch_related(
                "payments",
                Prefetch(
                    "lines",
                    queryset=SaleLine.objects.select_related(
                        "product",
                        "product_variant",
                    ),
                ),
            )
            .order_by(
                "-sold_at",
                "-created_at",
            )
        )