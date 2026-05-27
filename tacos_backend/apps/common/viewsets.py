from rest_framework import viewsets
from rest_framework.response import Response

from .utils import envelope_ok


class EnvelopeModelViewSet(viewsets.ModelViewSet):
    def finalize_response(self, request, response, *args, **kwargs):  # type: ignore[override]
        if isinstance(response, Response) and response.exception is False:
            data = response.data
            if isinstance(data, dict) and {"code", "message", "data"}.issubset(
                set(data.keys())
            ):
                return super().finalize_response(request, response, *args, **kwargs)
            response.data = envelope_ok(data if data is not None else {})
        return super().finalize_response(request, response, *args, **kwargs)
