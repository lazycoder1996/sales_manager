from django.db.models import Q

from apps.inventory.models import Student


class StudentService:

    @staticmethod
    def get_students(search=None):
        students = (
            Student.objects
            .filter(is_active=True)
            .select_related("house")
            .all()
        )

        if search:
            search = search.strip()

            if search:
                students = students.filter(
                    Q(admission_number__icontains=search)
                    | Q(firstname__icontains=search)
                    | Q(middlename__icontains=search)
                    | Q(surname__icontains=search)
                )

        return students

    @staticmethod
    def get_student(student_id):
        return (
            Student.objects
            .select_related("house")
            .filter(id=student_id, is_active=True)
            .first()
        )

    @staticmethod
    def create_student(validated_data):
        return Student.objects.create(
            **validated_data
        )

    @staticmethod
    def update_student(
        student,
        validated_data,
    ):
        for field, value in validated_data.items():
            setattr(
                student,
                field,
                value,
            )

        student.save()

        return student

    @staticmethod
    def deactivate_student(student):
        student.is_active = False
        student.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
        return student