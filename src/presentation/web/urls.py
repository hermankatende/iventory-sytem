from django.urls import path

from src.presentation.web.views.auth_views import (
    ForgotPasswordCompleteView,
    ForgotPasswordConfirmView,
    ForgotPasswordDoneView,
    ForgotPasswordView,
    LoginHistoryView,
    LoginView,
    PasswordChangeView,
    SecurityActivityView,
    logout_view,
)
from src.presentation.web.views.dashboard_view import dashboard
from src.presentation.web.views.inventory_views import (
    batch_operations_view,
    current_stock_view,
    inventory_history_view,
    inventory_transaction_view,
    product_category_view,
    product_registration_view,
    site_stock_view,
    stock_adjustment_view,
    stock_in_view,
    stock_out_view,
    stock_reports_view,
    transfer_between_sites_view,
)
from src.presentation.web.views.expense_views import expense_management_view
from src.presentation.web.views.payment_views import payment_create_view, supplier_outstanding_api
from src.presentation.web.views.site_context_views import switch_active_site_view
from src.presentation.web.views.reporting_views import (
    reporting_dashboard_view,
    reporting_export_csv_view,
    reporting_export_excel_view,
    reporting_export_pdf_view,
    reporting_print_view,
    supplier_ledger_view,
)
from src.presentation.web.views.receipt_views import (
    receipt_create_view,
    receipt_detail_view,
    receipt_list_view,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="password_reset"),
    path("auth/forgot-password/done/", ForgotPasswordDoneView.as_view(), name="password_reset_done"),
    path(
        "auth/reset/<uidb64>/<token>/",
        ForgotPasswordConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("auth/reset/complete/", ForgotPasswordCompleteView.as_view(), name="password_reset_complete"),
    path("auth/login-history/", LoginHistoryView.as_view(), name="login_history"),
    path("auth/security-activity/", SecurityActivityView.as_view(), name="security_activity"),
    path("inventory/products/", product_registration_view, name="inventory_products"),
    path("inventory/categories/", product_category_view, name="inventory_categories"),
    path("inventory/current-stock/", current_stock_view, name="inventory_current_stock"),
    path("inventory/transactions/", inventory_transaction_view, name="inventory_transaction_entry"),
    path("inventory/stock-in/", stock_in_view, name="inventory_stock_in"),
    path("inventory/stock-out/", stock_out_view, name="inventory_stock_out"),
    path("inventory/transfer/", transfer_between_sites_view, name="inventory_transfer"),
    path("inventory/adjustment/", stock_adjustment_view, name="inventory_adjustment"),
    path("inventory/history/", inventory_history_view, name="inventory_history"),
    path("inventory/batch-operations/", batch_operations_view, name="inventory_batch_operations"),
    path("inventory/reports/", stock_reports_view, name="inventory_stock_reports"),
    path("inventory/site-stock/", site_stock_view, name="site_stock"),
    path("receipts/", receipt_list_view, name="receipt_list"),
    path("receipts/create/", receipt_create_view, name="receipt_create"),
    path("receipts/<int:receipt_id>/", receipt_detail_view, name="receipt_detail"),
    path("payments/create/", payment_create_view, name="payment_create"),
    path("payments/outstanding/", supplier_outstanding_api, name="supplier_outstanding_api"),
    path("context/switch-site/", switch_active_site_view, name="switch_active_site"),
    path("expenses/", expense_management_view, name="expense_management"),
    path("reports/", reporting_dashboard_view, name="reporting_dashboard"),
    path("reports/export/csv/", reporting_export_csv_view, name="reporting_export_csv"),
    path("reports/export/excel/", reporting_export_excel_view, name="reporting_export_excel"),
    path("reports/export/pdf/", reporting_export_pdf_view, name="reporting_export_pdf"),
    path("reports/print/", reporting_print_view, name="reporting_print"),
    path("reports/supplier-ledger/", supplier_ledger_view, name="supplier_ledger"),
    path("", dashboard, name="dashboard"),
]
