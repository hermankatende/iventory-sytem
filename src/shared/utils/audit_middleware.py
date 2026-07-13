from src.application.audit.services.audit_trail_service import AuditTrailService
from src.infrastructure.persistence.repositories.audit_repository import DjangoAuditRepository


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.path.startswith("/api/"):
            service = AuditTrailService(repository=DjangoAuditRepository())
            service.record_event(
                actor=getattr(request.user, "username", "anonymous"),
                action=f"{request.method} {request.path}",
                metadata={"status_code": response.status_code},
            )
        return response
