from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.application.common.exceptions.domain_exceptions import NotFoundException, ValidationException
from src.application.expenses.services.expense_service import ExpenseService
from src.application.payments.services.payment_service import PaymentService
from src.application.procurement.services.receipt_service import ReceiptService
from src.application.reporting.services.report_service import ReportService
from src.infrastructure.persistence.models import Contract, Expense, ExpenseCategory, Invoice, Payment, Product, ProductPrice, Receipt, Supplier, Warehouse
from src.presentation.api.permissions.construction_rbac import ConstructionRBACPermission
from src.presentation.api.v1.serializers.erp_serializers import (
    ContractSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    PaymentCreateWithAllocationsSerializer,
    PaymentOutstandingQuerySerializer,
    ProductPriceSerializer,
    ProductSerializer,
    ReceiptCreateSerializer,
    ReceiptEditSerializer,
    ReceiptSerializer,
    SiteSerializer,
    SupplierSerializer,
)
from src.shared.utils.site_context import apply_site_scope, site_scope_from_request


class SiteListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SiteSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}

    def get_queryset(self):
        scope = site_scope_from_request(self.request)
        return apply_site_scope(
            Warehouse.objects.all().order_by("name"),
            field_name="id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )


class SupplierListCreateAPIView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by("name")
    serializer_class = SupplierSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related("item").all().order_by("product_code")
    serializer_class = ProductSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}


class ProductPriceListCreateAPIView(generics.ListCreateAPIView):
    queryset = ProductPrice.objects.select_related("product").all().order_by("-effective_date")
    serializer_class = ProductPriceSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}


class ReceiptListCreateAPIView(APIView):
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin", "ProjectManager"}

    def get(self, request):
        scope = site_scope_from_request(request)
        queryset = apply_site_scope(
            Receipt.objects.select_related("supplier", "warehouse").all().order_by("-created_at"),
            field_name="warehouse_id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )[:500]
        serializer = ReceiptSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReceiptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ReceiptService()
        data = serializer.validated_data

        receipt = service.create_receipt(
            receipt_number=data["receipt_number"],
            supplier_id=data["supplier_id"],
            warehouse_id=data["site_id"],
            source_type=data["source_type"],
            receipt_date=data["receipt_date"],
            notes=data.get("notes", ""),
            scan_file=None,
            lines=data["lines"],
            created_by=request.user,
        )
        out = ReceiptSerializer(receipt)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ReceiptDetailAPIView(APIView):
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin", "ProjectManager"}

    def get(self, request, receipt_id: int):
        receipt = get_object_or_404(Receipt, id=receipt_id)
        return Response(ReceiptSerializer(receipt).data)

    def put(self, request, receipt_id: int):
        return self._update(request, receipt_id)

    def patch(self, request, receipt_id: int):
        return self._update(request, receipt_id)

    def _update(self, request, receipt_id: int):
        serializer = ReceiptEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = ReceiptService()
        updates = {}
        if "supplier_id" in data:
            updates["supplier_id"] = data["supplier_id"]
        if "site_id" in data:
            updates["warehouse_id"] = data["site_id"]
        if "source_type" in data:
            updates["source_type"] = data["source_type"]
        if "receipt_date" in data:
            updates["receipt_date"] = data["receipt_date"]
        if "notes" in data:
            updates["notes"] = data["notes"]

        try:
            receipt = service.edit_receipt_header(
                receipt_id=receipt_id,
                editor=request.user,
                reason=data["reason_for_edit"],
                updates=updates,
            )
        except (ValidationException, NotFoundException) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReceiptSerializer(receipt).data)


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}

    def get_queryset(self):
        scope = site_scope_from_request(self.request)
        return apply_site_scope(
            Payment.objects.select_related("supplier", "site", "receipt", "invoice").all().order_by("-payment_date"),
            field_name="site_id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )


class ContractListCreateAPIView(generics.ListCreateAPIView):
    queryset = Contract.objects.select_related("supplier").all().order_by("-start_date")
    serializer_class = ContractSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin"}


class ExpenseCategoryListAPIView(generics.ListAPIView):
    queryset = ExpenseCategory.objects.filter(is_active=True).order_by("name")
    serializer_class = ExpenseCategorySerializer
    permission_classes = [ConstructionRBACPermission]


class ExpenseListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin", "ProjectManager"}

    def get_queryset(self):
        scope = site_scope_from_request(self.request)
        return apply_site_scope(
            Expense.objects.select_related("site", "category", "supplier").all().order_by("-date"),
            field_name="site_id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )

    def perform_create(self, serializer):
        service = ExpenseService()
        payload = serializer.validated_data
        scope = site_scope_from_request(self.request)
        requested_site_id = payload["site"].id
        site_qs = apply_site_scope(
            Warehouse.objects.filter(id=requested_site_id),
            field_name="id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )
        if not site_qs.exists():
            raise ValidationException("Selected site is outside your scope.")

        expense = service.create_expense(
            category_id=payload["category"].id,
            site_id=payload["site"].id,
            supplier_id=payload["supplier"].id if payload.get("supplier") else None,
            date=payload["date"],
            amount=float(payload["amount"]),
            description=payload.get("description", ""),
            attachment=None,
            created_by=self.request.user,
        )
        serializer.instance = expense


class InvoiceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin", "ProjectManager"}

    def get_queryset(self):
        scope = site_scope_from_request(self.request)
        return apply_site_scope(
            Invoice.objects.select_related("supplier", "site").all().order_by("-date"),
            field_name="site_id",
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )


class ReportsAPIView(APIView):
    permission_classes = [ConstructionRBACPermission]
    read_roles = {"Admin", "ProjectManager", "Accountant"}

    def get(self, request):
        scope = site_scope_from_request(request)
        report_type = (request.GET.get("type") or "").strip()
        site_id = request.GET.get("site_id")
        supplier_id = request.GET.get("supplier_id")
        start_date_raw = request.GET.get("start_date")
        end_date_raw = request.GET.get("end_date")

        try:
            start_date = date.fromisoformat(start_date_raw) if start_date_raw else None
            end_date = date.fromisoformat(end_date_raw) if end_date_raw else None
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        service = ReportService()
        report = service.generate_report(
            report_type=report_type,
            site_id=int(site_id) if site_id else None,
            supplier_id=int(supplier_id) if supplier_id else None,
            start_date=start_date,
            end_date=end_date,
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )
        return Response(report)


class PaymentOutstandingReceiptsAPIView(APIView):
    permission_classes = [ConstructionRBACPermission]
    read_roles = {"Admin", "ProjectManager", "Accountant"}

    def get(self, request):
        query = PaymentOutstandingQuerySerializer(data=request.GET)
        query.is_valid(raise_exception=True)

        scope = site_scope_from_request(request)
        service = PaymentService()
        rows = service.outstanding_receipts_for_supplier(
            supplier_id=query.validated_data["supplier_id"],
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )
        return Response({"rows": rows, "count": len(rows)})


class PaymentAllocationCreateAPIView(APIView):
    permission_classes = [ConstructionRBACPermission]
    write_roles = {"Admin", "Accountant", "ProjectManager"}

    def post(self, request):
        serializer = PaymentCreateWithAllocationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        scope = site_scope_from_request(request)
        selected_site_id = data.get("site_id")
        if selected_site_id:
            site_qs = apply_site_scope(
                Warehouse.objects.filter(id=selected_site_id),
                field_name="id",
                assigned_site_ids=scope["assigned_site_ids"],
                active_site_id=scope["active_site_id"],
            )
            if not site_qs.exists():
                return Response({"detail": "Selected site is outside your scope."}, status=status.HTTP_403_FORBIDDEN)

        service = PaymentService()
        try:
            payment = service.create_payment_with_allocations(
                supplier_id=data["supplier_id"],
                amount=data["amount"],
                payment_date=data.get("payment_date") or timezone.localdate(),
                method=data["method"],
                reference_number=data.get("reference_number", ""),
                allocations=data["allocations"],
                site_id=selected_site_id,
                assigned_site_ids=scope["assigned_site_ids"],
                active_site_id=scope["active_site_id"],
            )
        except ValidationException as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
