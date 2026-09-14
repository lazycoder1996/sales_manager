from django.http import JsonResponse
from django.utils import timezone


class APIResponse:
    @staticmethod
    def success(
        data=None,
        message="Success",
        status_code=200,
    ):
        return JsonResponse(
            {
                "data": data,
                "error": None,
                "success": True,
                "time": timezone.now().isoformat(),
                "message": message,
            },
            status=status_code,
        )

    @staticmethod
    def error(
        message="An error occurred",
        error=None,
        status_code=400,
    ):
        return JsonResponse(
            {
                "data": None,
                "error": error,
                "success": False,
                "time": timezone.now().isoformat(),
                "message": message,
            },
            status=status_code,
        )