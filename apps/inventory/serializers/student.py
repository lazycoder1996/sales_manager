from rest_framework import serializers

from apps.inventory.models import Student


class StudentSerializer(serializers.ModelSerializer):
    house_name = serializers.CharField(
        source="house.name",
        read_only=True,
    )

    house_code = serializers.CharField(
        source="house.code",
        read_only=True,
    )

    class Meta:
        model = Student
        fields = [
            "id",
            "admission_number",
            "firstname",
            "middlename",
            "surname",
            "fathers_name",
            "fathers_contact",
            "mothers_name",
            "mothers_contact",
            "residence",
            "date_of_birth",
            "house",
            "house_name",
            "house_code",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "house_name",
            "house_code",
            "created_at",
            "is_active",
            "updated_at",
        ]

    def validate_admission_number(
        self,
        value,
    ):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        queryset = Student.objects.filter(
            admission_number__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(
                id=self.instance.id,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A student with this admission number already exists."
            )

        return value