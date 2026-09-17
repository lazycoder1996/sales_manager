from rest_framework.views import APIView

from apps.core.responses import APIResponse

from apps.core.responses.pagination import CursorPagination
from apps.inventory.serializers.student import (
    StudentSerializer,
)
from apps.inventory.services.student import (
    StudentService,
)


class StudentListCreateView(APIView):

    def get(self, request):
        students = StudentService.get_students(
            search=request.query_params.get(
                "search"
            )
        )

        data = CursorPagination.paginate(
            queryset=students,
            request=request,
            serializer_class=StudentSerializer,
            ordering="-created_at",
        )

        return APIResponse.success(
            data=data,
            message="Students retrieved successfully.",
        )

    def post(self, request):
        serializer = StudentSerializer(
            data=request.data,
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Invalid student data.",
                error=serializer.errors,
                status_code=400,
            )

        student = StudentService.create_student(
            serializer.validated_data
        )

        serializer = StudentSerializer(
            student
        )

        return APIResponse.success(
            data=serializer.data,
            message="Student registered successfully.",
            status_code=201,
        )


class StudentDetailView(APIView):

    def get(self, request, student_id):
        student = StudentService.get_student(
            student_id
        )

        if student is None:
            return APIResponse.error(
                message="Student not found.",
                status_code=404,
            )

        serializer = StudentSerializer(
            student
        )

        return APIResponse.success(
            data=serializer.data,
            message="Student retrieved successfully.",
        )

    def patch(self, request, student_id):
        student = StudentService.get_student(
            student_id
        )

        if student is None:
            return APIResponse.error(
                message="Student not found.",
                status_code=404,
            )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return APIResponse.error(
                message="Invalid student data.",
                error=serializer.errors,
                status_code=400,
            )

        student = StudentService.update_student(
            student,
            serializer.validated_data,
        )

        serializer = StudentSerializer(
            student
        )

        return APIResponse.success(
            data=serializer.data,
            message="Student updated successfully.",
        )

    def delete(self, request, student_id):
        student = StudentService.get_student(student_id)

        if student is None:
            return APIResponse.error(
                message="Student not found.",
                status_code=404,
            )

        StudentService.deactivate_student(student)

        return APIResponse.success(
            message="Student deactivated successfully.",
        )