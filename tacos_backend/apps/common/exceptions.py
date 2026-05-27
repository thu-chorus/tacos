from typing import Any, Dict

from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):  # type: ignore[override]
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    data: Dict[str, Any] = {
        "code": response.status_code,
        "message": response.reason_phrase or "error",
        "data": (
            response.data
            if isinstance(response.data, dict)
            else {"detail": response.data}
        ),
    }
    response.data = data
    return response
