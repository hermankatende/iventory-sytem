from src.presentation.web.views.expense_views import expense_management_view
from src.presentation.web.views.payment_views import payment_create_view, supplier_outstanding_api
from src.presentation.web.views.receipt_views import (
    receipt_create_view,
    receipt_detail_view,
    receipt_list_view,
)

__all__ = [
    "receipt_list_view",
    "receipt_create_view",
    "receipt_detail_view",
    "payment_create_view",
    "supplier_outstanding_api",
    "expense_management_view",
]
