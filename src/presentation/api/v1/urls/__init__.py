from django.urls import path

from src.presentation.api.v1.views.erp_views import (
    ContractListCreateAPIView,
    ExpenseCategoryListAPIView,
    ExpenseListCreateAPIView,
    InvoiceListCreateAPIView,
    PaymentAllocationCreateAPIView,
    PaymentListCreateAPIView,
    PaymentOutstandingReceiptsAPIView,
    ProductListCreateAPIView,
    ProductPriceListCreateAPIView,
    ReceiptDetailAPIView,
    ReceiptListCreateAPIView,
    ReportsAPIView,
    SiteListCreateAPIView,
    SupplierListCreateAPIView,
)
from src.presentation.api.v1.views.inventory_views import StockAdjustmentAPIView

urlpatterns = [
    path("sites/", SiteListCreateAPIView.as_view(), name="api-sites"),
    path("suppliers/", SupplierListCreateAPIView.as_view(), name="api-suppliers"),
    path("products/", ProductListCreateAPIView.as_view(), name="api-products"),
    path("product-prices/", ProductPriceListCreateAPIView.as_view(), name="api-product-prices"),
    path("receipts/", ReceiptListCreateAPIView.as_view(), name="api-receipts"),
    path("receipts/<int:receipt_id>/", ReceiptDetailAPIView.as_view(), name="api-receipt-detail"),
    path("payments/", PaymentListCreateAPIView.as_view(), name="api-payments"),
    path("payments/outstanding-receipts/", PaymentOutstandingReceiptsAPIView.as_view(), name="api-payment-outstanding-receipts"),
    path("payments/allocate/", PaymentAllocationCreateAPIView.as_view(), name="api-payment-allocate"),
    path("contracts/", ContractListCreateAPIView.as_view(), name="api-contracts"),
    path("expenses/categories/", ExpenseCategoryListAPIView.as_view(), name="api-expense-categories"),
    path("expenses/", ExpenseListCreateAPIView.as_view(), name="api-expenses"),
    path("invoices/", InvoiceListCreateAPIView.as_view(), name="api-invoices"),
    path("reports/", ReportsAPIView.as_view(), name="api-reports"),
    path("inventory/adjust-stock/", StockAdjustmentAPIView.as_view(), name="adjust-stock"),
]
