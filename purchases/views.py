import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import models
from django.db.models import Q, Sum
from suppliers.models import Supplier
from products.models import Product, Warehouse, WarehouseStock
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GRNItem, Purchase
from .services import ProcurementService
from users.services import RBACService

class PurchaseOrderListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        qs = PurchaseOrder.objects.select_related('supplier', 'warehouse', 'created_by').all()

        search = request.GET.get('search')
        supplier_id = request.GET.get('supplier')
        warehouse_id = request.GET.get('warehouse')
        status_filter = request.GET.get('status')

        if search:
            qs = qs.filter(
                Q(po_number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(warehouse__name__icontains=search)
            )
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        if status_filter:
            qs = qs.filter(status=status_filter)

        total_pos = PurchaseOrder.objects.count()
        pending_approval = PurchaseOrder.objects.filter(status='pending_approval').count()
        approved_pos = PurchaseOrder.objects.filter(status='approved').count()
        partially_received = PurchaseOrder.objects.filter(status='partially_received').count()

        suppliers = Supplier.objects.filter(status='active')
        warehouses = Warehouse.objects.filter(status='active')

        context = {
            'orders': qs[:100],
            'total_pos': total_pos,
            'pending_approval': pending_approval,
            'approved_pos': approved_pos,
            'partially_received': partially_received,
            'suppliers': suppliers,
            'warehouses': warehouses,
            'search': search,
            'supplier_filter': supplier_id,
            'warehouse_filter': warehouse_id,
            'status_filter': status_filter,
            'active_menu': 'purchases'
        }
        return render(request, 'purchases/po_list.html', context)

class PurchaseOrderCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        suppliers = Supplier.objects.filter(status='active')
        warehouses = Warehouse.objects.filter(status='active')
        products = Product.objects.filter(status='active')

        context = {
            'auto_po_number': ProcurementService.generate_po_number(),
            'suppliers': suppliers,
            'warehouses': warehouses,
            'products': products,
            'active_menu': 'purchases'
        }
        return render(request, 'purchases/po_create.html', context)

    def post(self, request):
        po_number = request.POST.get('po_number') or ProcurementService.generate_po_number()
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        order_date = request.POST.get('order_date') or timezone.now().date()
        expected_delivery_date = request.POST.get('expected_delivery_date') or None
        payment_terms = request.POST.get('payment_terms', 'Net 30')
        notes = request.POST.get('notes', '')
        terms_conditions = request.POST.get('terms_conditions', '')

        supplier = get_object_or_404(Supplier, pk=supplier_id)
        warehouse = get_object_or_404(Warehouse, pk=warehouse_id)

        po = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier=supplier,
            warehouse=warehouse,
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            payment_terms=payment_terms,
            notes=notes,
            terms_conditions=terms_conditions,
            status='draft',
            created_by=request.user
        )

        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        rates = request.POST.getlist('rate[]')
        gsts = request.POST.getlist('gst[]')

        subtotal = 0
        total_tax = 0

        for i in range(len(product_ids)):
            try:
                prod = Product.objects.get(pk=product_ids[i])
                qty = int(quantities[i])
                rate = float(rates[i])
                gst_pct = float(gsts[i]) if gsts[i] else (prod.gst_rate or 0.0)
            except (ValueError, Product.DoesNotExist, IndexError):
                continue

            line_subtotal = qty * rate
            line_tax = line_subtotal * (gst_pct / 100.0)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            total_tax += line_tax

            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=prod,
                quantity=qty,
                rate=rate,
                gst_percent=gst_pct,
                total_amount=line_total
            )

        po.subtotal = subtotal
        po.tax_amount = total_tax
        po.grand_total = subtotal + total_tax
        po.save()

        # Check if submitted directly
        action_type = request.POST.get('action_type')
        if action_type == 'submit':
            ProcurementService.submit_po_for_approval(po, request.user)
            messages.success(request, f"Purchase Order '{po.po_number}' created and submitted for approval.")
        else:
            messages.success(request, f"Draft Purchase Order '{po.po_number}' saved successfully.")

        return redirect('po-detail', pk=po.id)

class PurchaseOrderDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'warehouse', 'created_by', 'approved_by').prefetch_related('items__product', 'grns'), pk=pk)
        
        # Calculate received comparison summary
        item_summary = []
        for item in po.items.all():
            rec_stats = GRNItem.objects.filter(grn__purchase_order=po, po_item=item, grn__status='confirmed').aggregate(
                rec=Sum('received_quantity'),
                acc=Sum('accepted_quantity'),
                rej=Sum('rejected_quantity'),
                dmg=Sum('damaged_quantity')
            )
            acc_qty = rec_stats['acc'] or 0
            item_summary.append({
                'item': item,
                'ordered': item.quantity,
                'received': rec_stats['rec'] or 0,
                'accepted': acc_qty,
                'rejected': rec_stats['rej'] or 0,
                'damaged': rec_stats['dmg'] or 0,
                'remaining': max(item.quantity - acc_qty, 0)
            })

        context = {
            'po': po,
            'item_summary': item_summary,
            'active_menu': 'purchases'
        }
        return render(request, 'purchases/po_detail.html', context)

    def post(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        if action == 'submit':
            ProcurementService.submit_po_for_approval(po, request.user)
            messages.success(request, f"Purchase Order '{po.po_number}' submitted for approval.")
        elif action == 'approve':
            ProcurementService.approve_po(po, request.user, notes=notes)
            messages.success(request, f"Purchase Order '{po.po_number}' approved successfully.")
        elif action == 'reject':
            ProcurementService.reject_po(po, request.user, notes=notes)
            messages.warning(request, f"Purchase Order '{po.po_number}' was rejected.")

        return redirect('po-detail', pk=po.id)

class PurchaseOrderPrintView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'warehouse', 'created_by').prefetch_related('items__product'), pk=pk)
        return render(request, 'purchases/po_print.html', {'po': po})

class GRNListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = GoodsReceiptNote.objects.select_related('purchase_order', 'supplier', 'warehouse', 'created_by').all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(grn_number__icontains=search) | Q(supplier__name__icontains=search) | Q(purchase_order__po_number__icontains=search))

        context = {
            'grns': qs[:100],
            'search': search,
            'active_menu': 'purchases'
        }
        return render(request, 'purchases/grn_list.html', context)

class GRNCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        po_id = request.GET.get('po')
        po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'warehouse').prefetch_related('items__product'), pk=po_id) if po_id else None

        suppliers = Supplier.objects.filter(status='active')
        warehouses = Warehouse.objects.filter(status='active')
        approved_pos = PurchaseOrder.objects.filter(status__in=['approved', 'partially_received'])

        context = {
            'auto_grn_number': ProcurementService.generate_grn_number(),
            'po': po,
            'approved_pos': approved_pos,
            'suppliers': suppliers,
            'warehouses': warehouses,
            'active_menu': 'purchases'
        }
        return render(request, 'purchases/grn_create.html', context)

    def post(self, request):
        grn_number = request.POST.get('grn_number') or ProcurementService.generate_grn_number()
        po_id = request.POST.get('purchase_order')
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        received_date = request.POST.get('received_date') or timezone.now().date()
        challan_number = request.POST.get('challan_number', '')
        invoice_number = request.POST.get('invoice_number', '')
        inspection_notes = request.POST.get('inspection_notes', '')

        po = PurchaseOrder.objects.filter(pk=po_id).first() if po_id else None
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        warehouse = get_object_or_404(Warehouse, pk=warehouse_id)

        grn = GoodsReceiptNote.objects.create(
            grn_number=grn_number,
            purchase_order=po,
            warehouse=warehouse,
            supplier=supplier,
            received_date=received_date,
            challan_number=challan_number,
            invoice_number=invoice_number,
            inspection_notes=inspection_notes,
            status='draft',
            created_by=request.user
        )

        po_item_ids = request.POST.getlist('po_item_id[]')
        product_ids = request.POST.getlist('product_id[]')
        received_qtys = request.POST.getlist('received_qty[]')
        accepted_qtys = request.POST.getlist('accepted_qty[]')
        damaged_qtys = request.POST.getlist('damaged_qty[]')
        batch_numbers = request.POST.getlist('batch_number[]')
        exp_dates = request.POST.getlist('expiry_date[]')
        serial_raws = request.POST.getlist('serials[]')

        for i in range(len(product_ids)):
            try:
                prod = Product.objects.get(pk=product_ids[i])
                rec_q = int(received_qtys[i])
                acc_q = int(accepted_qtys[i])
                dmg_q = int(damaged_qtys[i]) if damaged_qtys[i] else 0
                b_num = batch_numbers[i] if i < len(batch_numbers) else ''
                exp_d = exp_dates[i] if (i < len(exp_dates) and exp_dates[i]) else None
                s_list = [s.strip() for s in serial_raws[i].split(',') if s.strip()] if i < len(serial_raws) else []
                po_item = PurchaseOrderItem.objects.filter(pk=po_item_ids[i]).first() if (i < len(po_item_ids) and po_item_ids[i]) else None
            except (ValueError, Product.DoesNotExist, IndexError):
                continue

            ord_q = po_item.quantity if po_item else rec_q
            short_q = max(ord_q - rec_q, 0)
            rej_q = max(rec_q - acc_q, 0)
            rate_val = po_item.rate if po_item else (prod.purchase_price or 0.0)

            GRNItem.objects.create(
                grn=grn,
                po_item=po_item,
                product=prod,
                ordered_quantity=ord_q,
                received_quantity=rec_q,
                accepted_quantity=acc_q,
                rejected_quantity=rej_q,
                short_quantity=short_q,
                damaged_quantity=dmg_q,
                batch_number=b_num,
                expiry_date=exp_d,
                serial_numbers=s_list,
                rate=rate_val,
                line_total=acc_q * float(rate_val)
            )

        # Check if user wants to confirm immediately
        action_type = request.POST.get('action_type')
        if action_type == 'confirm':
            ProcurementService.confirm_grn(grn, request.user)
            messages.success(request, f"GRN '{grn.grn_number}' created and confirmed. Warehouse stock updated successfully!")
        else:
            messages.success(request, f"Draft GRN '{grn.grn_number}' saved successfully.")

        return redirect('grn-list')

class GRNConfirmView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        grn = get_object_or_404(GoodsReceiptNote, pk=pk)
        ProcurementService.confirm_grn(grn, request.user)
        messages.success(request, f"GRN '{grn.grn_number}' confirmed and warehouse stock updated.")
        return redirect('grn-list')

class GRNPrintView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        grn = get_object_or_404(GoodsReceiptNote.objects.select_related('purchase_order', 'supplier', 'warehouse', 'created_by').prefetch_related('items__product'), pk=pk)
        return render(request, 'purchases/grn_print.html', {'grn': grn})
