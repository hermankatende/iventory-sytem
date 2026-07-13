from django.urls import path

from apps.reports.views import (
    reporting_dashboard_view,
    reporting_export_csv_view,
    reporting_export_excel_view,
    reporting_export_pdf_view,
    reporting_print_view,
    supplier_ledger_view,
)

urlpatterns = [
    path("", reporting_dashboard_view, name="reporting_dashboard"),
    path("export/csv/", reporting_export_csv_view, name="reporting_export_csv"),
    path("export/excel/", reporting_export_excel_view, name="reporting_export_excel"),
    path("export/pdf/", reporting_export_pdf_view, name="reporting_export_pdf"),
    path("print/", reporting_print_view, name="reporting_print"),
    path("supplier-ledger/", supplier_ledger_view, name="supplier_ledger"),
]
