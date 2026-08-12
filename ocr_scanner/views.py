import os
import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone

from suppliers.models import Supplier
from products.models import Product, Warehouse
from purchases.models import Purchase, PurchaseItem
from .models import OCRScan, OCRScanItem, OCRScanAudit
from .forms import BillUploadForm, OCRVerificationForm
from .engine import OCRScannerEngine

def ocr_upload(request):
    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.user = request.user if request.user.is_authenticated else None
            doc = request.FILES['document']
            scan.original_filename = doc.name
            scan.file_size = doc.size
            ext = os.path.splitext(doc.name)[1].lower()
            scan.file_type = 'pdf' if ext == '.pdf' else 'image'
            scan.scan_id = f"SCAN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            scan.status = 'processing'
            scan.save()

            # Execute OCR Engine Extraction
            OCRScannerEngine.scan_document(scan)

            # Audit Log
            OCRScanAudit.objects.create(
                scan=scan,
                action="Document Uploaded & Scanned",
                user=request.user if request.user.is_authenticated else None,
                notes=f"Processed file '{doc.name}' ({scan.file_type})"
            )

            messages.success(request, f"Document '{doc.name}' scanned successfully. Please verify extracted data.")
            return redirect('ocr-verify', pk=scan.id)
        else:
            messages.error(request, "Failed to upload document. Please check file format and size limits.")
    else:
        form = BillUploadForm()

    recent_scans = OCRScan.objects.all()[:5]
    return render(request, 'ocr_scanner/scanner_upload.html', {
        'form': form,
        'recent_scans': recent_scans
    })

def ocr_verify(request, pk):
    scan = get_object_or_404(OCRScan, pk=pk)
    suppliers = Supplier.objects.filter(status='active')
    products = Product.objects.filter(status='active').select_related('unit')
    warehouses = Warehouse.objects.filter(status='active')

    # Check for Duplicate Invoice in Purchase Database
    duplicate_purchase = None
    if scan.matched_supplier and scan.invoice_number:
        duplicate_purchase = Purchase.objects.filter(
            supplier=scan.matched_supplier,
            invoice_number__iexact=scan.invoice_number
        ).first()

    if request.method == 'POST':
        form = OCRVerificationForm(request.POST, instance=scan)
        if form.is_valid():
            old_inv = scan.invoice_number
            scan = form.save()

            # Audit trail if invoice number edited
            if old_inv != scan.invoice_number:
                OCRScanAudit.objects.create(
                    scan=scan,
                    action="Field Corrected",
                    user=request.user if request.user.is_authenticated else None,
                    field_name="invoice_number",
                    old_value=old_inv,
                    new_value=scan.invoice_number
                )

            # Update item table inputs
            item_ids = request.POST.getlist('item_id[]')
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            rates = request.POST.getlist('rate[]')

            for i in range(len(item_ids)):
                try:
                    it_id = int(item_ids[i])
                    p_id = int(product_ids[i]) if product_ids[i] else None
                    qty = int(quantities[i])
                    rt = Decimal(rates[i])
                except (ValueError, IndexError):
                    continue

                item = OCRScanItem.objects.filter(pk=it_id, scan=scan).first()
                if item:
                    item.matched_product_id = p_id
                    item.quantity = qty
                    item.rate = rt
                    item.taxable_amount = Decimal(str(qty)) * rt
                    item.total_amount = item.taxable_amount * Decimal('1.18')
                    item.save()

            messages.success(request, f"Extracted data for scan '{scan.scan_id}' verified and updated.")

            if 'convert_to_purchase' in request.POST:
                return redirect('ocr-convert', pk=scan.id)

            return redirect('ocr-verify', pk=scan.id)
    else:
        form = OCRVerificationForm(instance=scan)

    items = scan.items.select_related('matched_product', 'matched_product__unit').all()
    audits = scan.audits.select_related('user').all()

    return render(request, 'ocr_scanner/scanner_verification.html', {
        'scan': scan,
        'form': form,
        'items': items,
        'audits': audits,
        'suppliers': suppliers,
        'products': products,
        'warehouses': warehouses,
        'duplicate_purchase': duplicate_purchase
    })

def ocr_convert_to_purchase(request, pk):
    scan = get_object_or_404(OCRScan, pk=pk)

    if scan.status == 'converted' and scan.created_purchase:
        messages.warning(request, f"Scan '{scan.scan_id}' has already been converted to Purchase '{scan.created_purchase.invoice_number}'.")
        return redirect('purchase-detail', pk=scan.created_purchase.id)

    if not scan.matched_supplier:
        messages.error(request, "Please select a matched Supplier before converting to Purchase.")
        return redirect('ocr-verify', pk=scan.id)

    wh = scan.warehouse or Warehouse.objects.first()

    inv_num = scan.invoice_number or f"INV-{scan.scan_id}"
    if Purchase.objects.filter(invoice_number=inv_num).exists():
        inv_num = f"{inv_num}-{timezone.now().strftime('%M%S')}"

    # Create Purchase Record
    purchase = Purchase.objects.create(
        invoice_number=inv_num,
        supplier=scan.matched_supplier,
        warehouse=wh,
        purchase_date=scan.invoice_date or timezone.now().date(),
        subtotal=scan.subtotal,
        tax_amount=scan.tax_amount,
        discount_amount=scan.discount_amount,
        grand_total=scan.grand_total,
        pending_amount=scan.grand_total,
        payment_status='pending',
        status='received',
        internal_notes=f"Created automatically from AI OCR Scan #{scan.scan_id}"
    )

    # Create Purchase Items
    for item in scan.items.all():
        if item.matched_product:
            PurchaseItem.objects.create(
                purchase=purchase,
                product=item.matched_product,
                quantity=item.quantity,
                free_quantity=item.free_quantity,
                rate=item.rate,
                discount_percent=item.discount_percent,
                discount_amount=Decimal('0.00'),
                gst_percent=item.gst_percent,
                gst_amount=item.total_amount - item.taxable_amount,
                taxable_amount=item.taxable_amount,
                total_amount=item.total_amount
            )

    # Update scan
    scan.created_purchase = purchase
    scan.status = 'converted'
    scan.save()

    # Log audit
    OCRScanAudit.objects.create(
        scan=scan,
        action="Converted to Purchase Invoice",
        user=request.user if request.user.is_authenticated else None,
        notes=f"Linked to Purchase ID #{purchase.id} ({purchase.invoice_number})"
    )

    messages.success(request, f"Scan '{scan.scan_id}' successfully converted to Purchase Invoice '{purchase.invoice_number}'.")
    return redirect('purchase-detail', pk=purchase.id)

class OCRHistoryListView(ListView):
    model = OCRScan
    template_name = 'ocr_scanner/scan_history.html'
    context_object_name = 'scans'
    paginate_by = 10

    def get_queryset(self):
        qs = OCRScan.objects.select_related('matched_supplier', 'warehouse', 'user', 'created_purchase').all()

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(scan_id__icontains=q) |
                Q(original_filename__icontains=q) |
                Q(invoice_number__icontains=q) |
                Q(supplier_raw_name__icontains=q) |
                Q(matched_supplier__name__icontains=q)
            ).distinct()

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_scans = OCRScan.objects.all()

        context['summary'] = {
            'total_scans': all_scans.count(),
            'high_confidence_count': all_scans.filter(overall_confidence__gte=Decimal('80.00')).count(),
            'needs_review_count': all_scans.filter(status='needs_review').count(),
            'converted_count': all_scans.filter(status='converted').count(),
        }

        context['statuses'] = OCRScan.STATUS_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context

class OCRScanDetailView(DetailView):
    model = OCRScan
    template_name = 'ocr_scanner/scan_detail.html'
    context_object_name = 'scan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scan = self.get_object()
        context['items'] = scan.items.select_related('matched_product', 'matched_product__unit').all()
        context['audits'] = scan.audits.select_related('user').all()
        return context

def export_ocr_scans_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ocr_scan_history.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Scan ID', 'Filename', 'File Type', 'Invoice Number', 'Invoice Date',
        'Supplier', 'Grand Total', 'Confidence %', 'Status', 'Created At'
    ])

    scans = OCRScan.objects.select_related('matched_supplier').all()
    for s in scans:
        writer.writerow([
            s.scan_id,
            s.original_filename,
            s.get_file_type_display(),
            s.invoice_number,
            s.invoice_date.strftime('%Y-%m-%d') if s.invoice_date else '',
            s.matched_supplier.name if s.matched_supplier else s.supplier_raw_name,
            s.grand_total,
            f"{s.overall_confidence}%",
            s.get_status_display(),
            s.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response
