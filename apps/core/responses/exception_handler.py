import traceback

from rest_framework.views import exception_handler as drf_exception_handler

from apps.core.responses import APIResponse


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        print("\n===== UNEXPECTED ERROR =====")
        traceback.print_exc()
        print("============================\n")

        return APIResponse.error(
            error="An unexpected error occurred.",
            message="Internal server error.",
            status_code=500,
        )

    if isinstance(response.data, dict):
        error = response.data
    else:
        error = response.data

    message = "An error occurred."

    if response.status_code == 400:
        message = "Validation error."
    elif response.status_code == 401:
        message = "Authentication required."
    elif response.status_code == 403:
        message = "You do not have permission to perform this action."
    elif response.status_code == 404:
        message = "Resource not found."
    elif response.status_code == 405:
        message = "Method not allowed."
    elif response.status_code >= 500:
        message = "Internal server error."

    return APIResponse.error(
        error=error,
        message=message,
        status_code=response.status_code,
    )