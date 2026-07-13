from django.urls import path

from apps.purchases.views import (
    expense_management_view,
    payment_create_view,
    receipt_create_view,
    receipt_detail_view,
    receipt_list_view,
    supplier_outstanding_api,
)

urlpatterns = [
    path("receipts/", receipt_list_view, name="receipt_list"),
    path("receipts/create/", receipt_create_view, name="receipt_create"),
    path("receipts/<int:receipt_id>/", receipt_detail_view, name="receipt_detail"),
    path("payments/create/", payment_create_view, name="payment_create"),
    path("payments/outstanding/", supplier_outstanding_api, name="supplier_outstanding_api"),
    path("expenses/", expense_management_view, name="expense_management"),
]
