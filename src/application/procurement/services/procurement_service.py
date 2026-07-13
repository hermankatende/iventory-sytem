class ProcurementService:
    def submit_purchase_order(self, po_data: dict) -> dict:
        return {"status": "SUBMITTED", "purchase_order": po_data}
