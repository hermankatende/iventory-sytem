from src.application.common.interfaces.repositories import SupplierRepository


class SupplierService:
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository

    def list_active_suppliers(self) -> list[dict]:
        return self.supplier_repository.list_active_suppliers()
