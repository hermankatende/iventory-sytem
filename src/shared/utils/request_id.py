import threading
import uuid


_local = threading.local()


def get_request_id() -> str:
    return getattr(_local, "request_id", "-")


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = _local.request_id
        return self.get_response(request)
