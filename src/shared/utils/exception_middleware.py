import logging

from django.http import JsonResponse


logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            logger.exception("Unhandled exception", extra={"request_id": getattr(request, "request_id", "-")})
            return JsonResponse({"error": "Internal server error"}, status=500)
