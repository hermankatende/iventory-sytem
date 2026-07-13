from django.urls import path

from apps.inventory.views import (
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

urlpatterns = [
    path("products/", product_registration_view, name="inventory_products"),
    path("categories/", product_category_view, name="inventory_categories"),
    path("current-stock/", current_stock_view, name="inventory_current_stock"),
    path("transactions/", inventory_transaction_view, name="inventory_transaction_entry"),
    path("stock-in/", stock_in_view, name="inventory_stock_in"),
    path("stock-out/", stock_out_view, name="inventory_stock_out"),
    path("transfer/", transfer_between_sites_view, name="inventory_transfer"),
    path("adjustment/", stock_adjustment_view, name="inventory_adjustment"),
    path("history/", inventory_history_view, name="inventory_history"),
    path("batch-operations/", batch_operations_view, name="inventory_batch_operations"),
    path("reports/", stock_reports_view, name="inventory_stock_reports"),
    path("site-stock/", site_stock_view, name="site_stock"),
]
