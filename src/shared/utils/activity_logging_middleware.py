from src.application.audit.services.audit_trail_service import AuditTrailService
from src.infrastructure.persistence.models import UserActivityLog
from src.infrastructure.persistence.repositories.audit_repository import DjangoAuditRepository


class ActivityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/static/"):
            return response

        actor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        try:
            UserActivityLog.objects.create(
                user=actor,
                action=f"{request.method} {request.path}",
                path=request.path[:255],
                method=request.method,
                metadata={"status_code": response.status_code},
            )

            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                service = AuditTrailService(repository=DjangoAuditRepository())
                service.record_event(
                    actor=getattr(request.user, "username", "anonymous"),
                    action=f"{request.method} {request.path}",
                    metadata={"status_code": response.status_code},
                )
        except Exception:
            # Keep requests non-blocking if log persistence is unavailable.
            pass

        return response
