from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from src.infrastructure.persistence.models import ExpenseCategory


class Command(BaseCommand):
    help = "Seed construction ERP roles and expense categories."

    ROLE_PERMISSIONS = {
        "Admin": [
            ("persistence", "add_receipt"),
            ("persistence", "change_receipt"),
            ("persistence", "delete_receipt"),
            ("persistence", "view_receipt"),
            ("persistence", "add_invoice"),
            ("persistence", "change_invoice"),
            ("persistence", "delete_invoice"),
            ("persistence", "view_invoice"),
            ("persistence", "add_expense"),
            ("persistence", "change_expense"),
            ("persistence", "delete_expense"),
            ("persistence", "view_expense"),
            ("persistence", "add_payment"),
            ("persistence", "change_payment"),
            ("persistence", "delete_payment"),
            ("persistence", "view_payment"),
            ("persistence", "view_auditlog"),
            ("persistence", "view_supplier"),
            ("persistence", "add_supplier"),
            ("persistence", "change_supplier"),
            ("persistence", "delete_supplier"),
            ("persistence", "view_warehouse"),
            ("persistence", "add_warehouse"),
            ("persistence", "change_warehouse"),
            ("persistence", "delete_warehouse"),
            ("persistence", "view_contract"),
            ("persistence", "add_contract"),
            ("persistence", "change_contract"),
            ("persistence", "delete_contract"),
            ("persistence", "view_product"),
            ("persistence", "add_product"),
            ("persistence", "change_product"),
            ("persistence", "delete_product"),
            ("persistence", "view_productprice"),
            ("persistence", "add_productprice"),
            ("persistence", "change_productprice"),
            ("persistence", "delete_productprice"),
            ("auth", "view_user"),
            ("auth", "add_user"),
            ("auth", "change_user"),
            ("auth", "delete_user"),
        ],
        "ProjectManager": [
            ("persistence", "view_receipt"),
            ("persistence", "add_receipt"),
            ("persistence", "change_receipt"),
            ("persistence", "view_invoice"),
            ("persistence", "add_invoice"),
            ("persistence", "change_invoice"),
            ("persistence", "view_expense"),
            ("persistence", "add_expense"),
            ("persistence", "change_expense"),
            ("persistence", "view_payment"),
            ("persistence", "view_supplier"),
            ("persistence", "view_warehouse"),
            ("persistence", "view_contract"),
            ("persistence", "view_product"),
            ("persistence", "view_productprice"),
            ("persistence", "view_auditlog"),
        ],
        "Accountant": [
            ("persistence", "view_receipt"),
            ("persistence", "view_invoice"),
            ("persistence", "view_expense"),
            ("persistence", "view_payment"),
            ("persistence", "view_supplier"),
            ("persistence", "view_warehouse"),
            ("persistence", "view_contract"),
            ("persistence", "view_product"),
            ("persistence", "view_productprice"),
            ("persistence", "view_auditlog"),
        ],
        "SiteEngineer": [
            ("persistence", "view_receipt"),
            ("persistence", "view_invoice"),
            ("persistence", "view_expense"),
            ("persistence", "view_payment"),
            ("persistence", "view_supplier"),
            ("persistence", "view_warehouse"),
            ("persistence", "view_contract"),
            ("persistence", "view_product"),
            ("persistence", "view_productprice"),
            ("persistence", "view_item"),
            ("persistence", "view_stocklevel"),
            ("persistence", "view_stockmovement"),
        ],
    }

    EXPENSE_CATEGORIES = [
        ("BUYING_MATERIALS", "Buying Materials"),
        ("FUEL", "Fuel"),
        ("LABOUR", "Labour"),
        ("TRANSPORT", "Transport"),
        ("ACCOMMODATION", "Accommodation"),
        ("REPAIRS", "Repairs"),
        ("CONTRACTOR_PAYMENT", "Contractor Payment"),
        ("EQUIPMENT", "Equipment"),
    ]

    def handle(self, *args, **options):
        self._seed_roles()
        self._seed_expense_categories()
        self.stdout.write(self.style.SUCCESS("Construction ERP seed complete."))

    def _seed_roles(self):
        for role, permission_refs in self.ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.clear()
            for app_label, codename in permission_refs:
                permission = Permission.objects.filter(codename=codename, content_type__app_label=app_label).first()
                if permission:
                    group.permissions.add(permission)
            self.stdout.write(self.style.NOTICE(f"Seeded role: {role}"))

    def _seed_expense_categories(self):
        for code, name in self.EXPENSE_CATEGORIES:
            ExpenseCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_active": True},
            )
        self.stdout.write(self.style.NOTICE("Seeded expense categories."))
