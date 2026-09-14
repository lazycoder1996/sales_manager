from rest_framework.views import APIView

from apps.core.responses import APIResponse
from apps.inventory.serializers.student_history import (
    StudentHistorySerializer,
)
from apps.inventory.services.student_history import (
    StudentHistoryService,
)


class StudentHistoryView(APIView):

    def get(self, request):
        student_number = request.query_params.get(
            "student_number"
        )

        if not student_number:
            return APIResponse.error(
                error={
                    "student_number": (
                        "Student number is required."
                    )
                },
                message="Student number is required.",
                status_code=400,
            )

        sales = list(
            StudentHistoryService.get_by_student_number(
                student_number
            )
        )

        if not sales:
            return APIResponse.error(
                message="Student not found.",
                status_code=404,
            )

        data = StudentHistorySerializer({
            "student_number": sales[0].student_number,
            "student_name": sales[0].student_name,
            "sales": sales,
        }).data

        return APIResponse.success(
            data=data,
        )