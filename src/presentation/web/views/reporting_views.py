import csv
from datetime import timedelta
from io import BytesIO, StringIO

from django.db.models import DecimalField, F, Value
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from src.application.reporting.services.report_service import ReportService
from src.infrastructure.persistence.models import Payment, Receipt, Supplier
from src.presentation.web.forms.reporting_forms import ReportingFilterForm
from src.shared.utils.site_context import site_scope_from_request, switchable_sites_for_user


report_service = ReportService()


def _reporting_form_data(request):
    data = request.GET.copy()
    if not data.get("report_type"):
        data["report_type"] = "expenses_monthly"
    if not data.get("period"):
        data["period"] = "monthly"
    return data


def _resolve_period_dates(period: str, start_date, end_date):
    today = timezone.localdate()
    period = (period or "custom").lower()
    if period == "daily":
        return today, today
    if period == "weekly":
        return today - timedelta(days=6), today
    if period == "monthly":
        return today.replace(day=1), today
    return start_date, end_date


def _form_site_supplier_qs(request, scope):
    site_qs = switchable_sites_for_user(request.user)
    supplier_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        supplier_qs = supplier_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        supplier_qs = supplier_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()
    return site_qs, supplier_qs


def _build_report_bundle(form: ReportingFilterForm, scope: dict):
    cleaned = getattr(form, "cleaned_data", {})
    period = cleaned.get("period") or "custom"
    start_date, end_date = _resolve_period_dates(period, cleaned.get("start_date"), cleaned.get("end_date"))

    site_id = cleaned["site"].id if cleaned.get("site") else None
    supplier_id = cleaned["supplier"].id if cleaned.get("supplier") else None

    def run(report_type: str):
        return report_service.generate_report(
            report_type=report_type,
            site_id=site_id,
            supplier_id=supplier_id,
            start_date=start_date,
            end_date=end_date,
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "expenses_daily": run("expenses_daily"),
        "expenses_weekly": run("expenses_weekly"),
        "expenses_monthly": run("expenses_monthly"),
        "supplier_balance": run("supplier_balance"),
        "products_bought": run("products_bought"),
        "outstanding_supplier_balances": run("outstanding_supplier_balances"),
        "site_expense_summary": run("site_expense_summary"),
        "receipt_history_log": run("receipt_history_log"),
    }


@login_required
@require_http_methods(["GET"])
def reporting_dashboard_view(request):
    scope = site_scope_from_request(request)
    site_qs, supplier_qs = _form_site_supplier_qs(request, scope)

    form = ReportingFilterForm(
        _reporting_form_data(request),
        site_queryset=site_qs,
        supplier_queryset=supplier_qs,
    )
    form.is_valid()

    bundle = _build_report_bundle(form, scope)

    def chart_payload(report_key):
        rows = bundle[report_key]["rows"]
        return {
            "labels": [str(row.get("period", "")) for row in rows],
            "values": [float(row.get("total", 0)) for row in rows],
        }

    active_tab = request.GET.get("tab") or "expenses"

    return render(
        request,
        "reports/reporting_dashboard.html",
        {
            "form": form,
            "active_tab": active_tab,
            "bundle": bundle,
            "daily_chart": chart_payload("expenses_daily"),
            "weekly_chart": chart_payload("expenses_weekly"),
            "monthly_chart": chart_payload("expenses_monthly"),
        },
    )


@login_required
@require_http_methods(["GET"])
def reporting_export_csv_view(request):
    scope = site_scope_from_request(request)
    site_qs, supplier_qs = _form_site_supplier_qs(request, scope)
    form = ReportingFilterForm(_reporting_form_data(request), site_queryset=site_qs, supplier_queryset=supplier_qs)
    form.is_valid()

    cleaned = getattr(form, "cleaned_data", {})
    period = cleaned.get("period") or "custom"
    start_date, end_date = _resolve_period_dates(period, cleaned.get("start_date"), cleaned.get("end_date"))

    report_type = cleaned.get("report_type") or "expenses_monthly"
    report_data = report_service.generate_report(
        report_type=report_type,
        site_id=cleaned["site"].id if cleaned.get("site") else None,
        supplier_id=cleaned["supplier"].id if cleaned.get("supplier") else None,
        start_date=start_date,
        end_date=end_date,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )

    output = StringIO()
    writer = csv.writer(output)

    rows = report_data["rows"]
    if rows:
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])
    else:
        writer.writerow(["No rows"])

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename=report_{report_type}.csv"
    return response


@login_required
@require_http_methods(["GET"])
def reporting_export_excel_view(request):
    from openpyxl import Workbook

    scope = site_scope_from_request(request)
    site_qs, supplier_qs = _form_site_supplier_qs(request, scope)
    form = ReportingFilterForm(_reporting_form_data(request), site_queryset=site_qs, supplier_queryset=supplier_qs)
    form.is_valid()

    cleaned = getattr(form, "cleaned_data", {})
    period = cleaned.get("period") or "custom"
    start_date, end_date = _resolve_period_dates(period, cleaned.get("start_date"), cleaned.get("end_date"))

    report_type = cleaned.get("report_type") or "expenses_monthly"
    report_data = report_service.generate_report(
        report_type=report_type,
        site_id=cleaned["site"].id if cleaned.get("site") else None,
        supplier_id=cleaned["supplier"].id if cleaned.get("supplier") else None,
        start_date=start_date,
        end_date=end_date,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = report_data["report_type"][:31]

    rows = report_data["rows"]
    if rows:
        headers = list(rows[0].keys())
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get(h, "") for h in headers])
    else:
        sheet.append(["No rows"])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename=report_{report_type}.xlsx"
    return response


@login_required
@require_http_methods(["GET"])
def reporting_export_pdf_view(request):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    scope = site_scope_from_request(request)
    site_qs, supplier_qs = _form_site_supplier_qs(request, scope)
    form = ReportingFilterForm(_reporting_form_data(request), site_queryset=site_qs, supplier_queryset=supplier_qs)
    form.is_valid()

    cleaned = getattr(form, "cleaned_data", {})
    period = cleaned.get("period") or "custom"
    start_date, end_date = _resolve_period_dates(period, cleaned.get("start_date"), cleaned.get("end_date"))

    report_type = cleaned.get("report_type") or "expenses_monthly"
    report_data = report_service.generate_report(
        report_type=report_type,
        site_id=cleaned["site"].id if cleaned.get("site") else None,
        supplier_id=cleaned["supplier"].id if cleaned.get("supplier") else None,
        start_date=start_date,
        end_date=end_date,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, f"Report: {report_data['report_type']}")
    y -= 20
    pdf.setFont("Helvetica", 9)

    rows = report_data["rows"]
    if not rows:
        pdf.drawString(40, y, "No data")
    else:
        headers = list(rows[0].keys())
        pdf.drawString(40, y, " | ".join(headers)[:150])
        y -= 14
        for row in rows[:80]:
            if y < 40:
                pdf.showPage()
                y = height - 40
            pdf.drawString(40, y, " | ".join(str(row.get(h, "")) for h in headers)[:150])
            y -= 12

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=report_{report_data['report_type']}.pdf"
    return response


@login_required
@require_http_methods(["GET"])
def reporting_print_view(request):
    scope = site_scope_from_request(request)
    site_qs, supplier_qs = _form_site_supplier_qs(request, scope)
    form = ReportingFilterForm(_reporting_form_data(request), site_queryset=site_qs, supplier_queryset=supplier_qs)
    form.is_valid()

    cleaned = getattr(form, "cleaned_data", {})
    period = cleaned.get("period") or "custom"
    start_date, end_date = _resolve_period_dates(period, cleaned.get("start_date"), cleaned.get("end_date"))

    report_type = cleaned.get("report_type") or "expenses_monthly"
    report_data = report_service.generate_report(
        report_type=report_type,
        site_id=cleaned["site"].id if cleaned.get("site") else None,
        supplier_id=cleaned["supplier"].id if cleaned.get("supplier") else None,
        start_date=start_date,
        end_date=end_date,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )

    return render(request, "reports/report_print.html", {"report_data": report_data})


@login_required
@require_http_methods(["GET"])
def supplier_ledger_view(request):
    scope = site_scope_from_request(request)
    site_qs = switchable_sites_for_user(request.user)
    supplier_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        supplier_qs = supplier_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        supplier_qs = supplier_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()

    supplier_id = request.GET.get("supplier_id")
    site_id = request.GET.get("site_id")

    selected_supplier_id = int(supplier_id) if supplier_id and supplier_id.isdigit() else None
    selected_site_id = int(site_id) if site_id and site_id.isdigit() else None

    receipt_rows = Receipt.objects.select_related("supplier", "warehouse")
    payment_rows = Payment.objects.select_related("supplier", "site", "invoice")

    if selected_supplier_id:
        receipt_rows = receipt_rows.filter(supplier_id=selected_supplier_id)
        payment_rows = payment_rows.filter(supplier_id=selected_supplier_id)

    if selected_site_id:
        receipt_rows = receipt_rows.filter(warehouse_id=selected_site_id)
        payment_rows = payment_rows.filter(site_id=selected_site_id)
    elif scope["active_site_id"]:
        receipt_rows = receipt_rows.filter(warehouse_id=scope["active_site_id"])
        payment_rows = payment_rows.filter(site_id=scope["active_site_id"])
    elif scope["assigned_site_ids"] is not None:
        receipt_rows = receipt_rows.filter(warehouse_id__in=scope["assigned_site_ids"])
        payment_rows = payment_rows.filter(site_id__in=scope["assigned_site_ids"])

    receipt_rows = receipt_rows.values(
        transaction_date=F("receipt_date"),
        sort_order=Value(0),
        transaction_id=F("id"),
        invoice_no=F("receipt_number"),
        purchase_total=F("total_amount"),
        payment_total=Value(0, output_field=DecimalField(max_digits=14, decimal_places=2)),
        row_type=Value("DEBIT"),
        supplier_name=F("supplier__name"),
    )
    payment_rows = payment_rows.values(
        transaction_date=F("payment_date"),
        sort_order=Value(1),
        transaction_id=F("id"),
        invoice_no=Coalesce(F("invoice__invoice_number"), F("reference_number"), F("reference"), Value("")),
        purchase_total=Value(0, output_field=DecimalField(max_digits=14, decimal_places=2)),
        payment_total=F("amount"),
        row_type=Value("CREDIT"),
        supplier_name=F("supplier__name"),
    )

    ledger = list(receipt_rows.union(payment_rows, all=True).order_by("transaction_date", "sort_order", "transaction_id"))
    running_balance = 0.0
    for row in ledger:
        purchase_total = float(row.get("purchase_total") or 0)
        payment_total = float(row.get("payment_total") or 0)
        running_balance += purchase_total - payment_total
        row["balance_outstanding"] = running_balance

    return render(
        request,
        "reports/supplier_ledger.html",
        {
            "rows": ledger,
            "suppliers": supplier_qs,
            "sites": site_qs,
            "selected_supplier_id": selected_supplier_id,
            "selected_site_id": selected_site_id,
        },
    )
