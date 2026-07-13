from src.application.common.interfaces.repositories import SupplierRepository
from src.infrastructure.persistence.models import Supplier


class DjangoSupplierRepository(SupplierRepository):
    def list_active_suppliers(self) -> list[dict]:
        return list(
            Supplier.objects.all()
            .values("id", "name", "email", "phone", "address", "created_at")
            .order_by("name")
        )
