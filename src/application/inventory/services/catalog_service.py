from django.db import transaction

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.infrastructure.persistence.models import Item, Product, ProductCategory


class ProductCatalogService:
    @transaction.atomic
    def register_category(self, name: str, description: str = "") -> ProductCategory:
        name = (name or "").strip()
        if not name:
            raise ValidationException("Category name is required")
        category, _ = ProductCategory.objects.get_or_create(name=name, defaults={"description": description})
        return category

    @transaction.atomic
    def register_product(
        self,
        *,
        sku: str,
        name: str,
        reorder_level: int,
        unit_cost: float,
        product_code: str,
        category_id: int | None = None,
        barcode: str = "",
        unit_of_measure: str = "unit",
    ) -> Product:
        sku = (sku or "").strip()
        name = (name or "").strip()
        product_code = (product_code or "").strip()

        if not sku or not name or not product_code:
            raise ValidationException("SKU, name, and product code are required")
        if reorder_level < 0:
            raise ValidationException("Reorder level cannot be negative")
        if unit_cost < 0:
            raise ValidationException("Unit cost cannot be negative")

        category = ProductCategory.objects.filter(id=category_id).first() if category_id else None

        item, _ = Item.objects.get_or_create(
            sku=sku,
            defaults={
                "name": name,
                "reorder_level": reorder_level,
                "unit_cost": unit_cost,
                "barcode": barcode,
                "is_active": True,
            },
        )

        item.name = name
        item.reorder_level = reorder_level
        item.unit_cost = unit_cost
        item.barcode = barcode
        item.save(update_fields=["name", "reorder_level", "unit_cost", "barcode"])

        product, _ = Product.objects.get_or_create(
            item=item,
            defaults={
                "category": category,
                "product_code": product_code,
                "barcode": barcode,
                "is_barcode_ready": bool(barcode),
                "unit_of_measure": unit_of_measure,
            },
        )

        product.category = category
        product.product_code = product_code
        product.barcode = barcode
        product.is_barcode_ready = bool(barcode)
        product.unit_of_measure = unit_of_measure or "unit"
        product.save(update_fields=["category", "product_code", "barcode", "is_barcode_ready", "unit_of_measure"])

        return product

    def search_products(self, search: str = "", category_id: int | None = None, active_only: bool = True) -> list[dict]:
        queryset = Product.objects.select_related("item", "category")
        if active_only:
            queryset = queryset.filter(item__is_active=True)
        if search:
            queryset = queryset.filter(
                item__name__icontains=search,
            ) | queryset.filter(
                item__sku__icontains=search,
            ) | queryset.filter(
                product_code__icontains=search,
            ) | queryset.filter(
                barcode__icontains=search,
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return [
            {
                "item_id": product.item_id,
                "product_id": product.id,
                "name": product.item.name,
                "sku": product.item.sku,
                "product_code": product.product_code,
                "barcode": product.barcode,
                "barcode_ready": product.is_barcode_ready,
                "category": product.category.name if product.category else "",
                "reorder_level": product.item.reorder_level,
                "unit_cost": float(product.item.unit_cost),
                "unit_of_measure": product.unit_of_measure,
            }
            for product in queryset.order_by("item__name")
        ]
