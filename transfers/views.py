import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone

from products.models import Product, Warehouse, WarehouseStock
from inventory.models import StockMovement
from inventory.views import update_product_total_stock
from .models import StockTransfer, StockTransferItem, StockTransferHistory
from .forms import StockTransferForm, StockTransferRejectForm

class TransferListView(ListView):
    model = StockTransfer
    template_name = 'transfers/transfer_list.html'
    context_object_name = 'transfers'
    paginate_by = 10

    def get_queryset(self):
        qs = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse', 'requested_by', 'received_by').all()

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(transfer_number__icontains=q) |
                Q(from_warehouse__name__icontains=q) |
                Q(to_warehouse__name__icontains=q) |
                Q(items__product__name__icontains=q) |
                Q(items__product__sku__icontains=q)
            ).distinct()

        from_wh = self.request.GET.get('from_warehouse')
        if from_wh:
            qs = qs.filter(from_warehouse_id=from_wh)

        to_wh = self.request.GET.get('to_warehouse')
        if to_wh:
            qs = qs.filter(to_warehouse_id=to_wh)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_transfers = StockTransfer.objects.all()

        context['summary'] = {
            'total_transfers': all_transfers.count(),
            'in_transit_count': all_transfers.filter(status='in_transit').count(),
            'completed_count': all_transfers.filter(status__in=['received', 'partially_received']).count(),
            'draft_count': all_transfers.filter(status='draft').count(),
        }

        context['warehouses'] = Warehouse.objects.filter(status='active')
        context['statuses'] = StockTransfer.STATUS_CHOICES
        context['selected_from_wh'] = self.request.GET.get('from_warehouse', '')
        context['selected_to_wh'] = self.request.GET.get('to_warehouse', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')

        return context

class TransferDetailView(DetailView):
    model = StockTransfer
    template_name = 'transfers/transfer_detail.html'
    context_object_name = 'transfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = self.get_object()
        context['items'] = transfer.items.select_related('product', 'product__unit').all()
        context['history'] = transfer.history.select_related('user').all()
        return context

def transfer_create(request):
    warehouses = Warehouse.objects.filter(status='active')
    products = Product.objects.filter(status='active').select_related('unit')

    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.requested_by = request.user if request.user.is_authenticated else None

            # Parse items from POST
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            remarks_list = request.POST.getlist('remarks[]')

            if not product_ids:
                messages.error(request, "Please add at least one product to transfer.")
                return render(request, 'transfers/transfer_form.html', {
                    'form': form, 'warehouses': warehouses, 'products': products, 'title': 'Create Stock Transfer'
                })

            # Check stock availability for each product at from_warehouse
            item_data = []
            total_qty = 0
            has_error = False

            for i in range(len(product_ids)):
                try:
                    p_id = int(product_ids[i])
                    qty = int(quantities[i])
                    rem = remarks_list[i] if i < len(remarks_list) else ""
                except (ValueError, IndexError):
                    continue

                if qty <= 0:
                    continue

                prod = Product.objects.filter(pk=p_id).first()
                if not prod:
                    continue

                stock_obj = WarehouseStock.objects.filter(product=prod, warehouse=transfer.from_warehouse).first()
                available = stock_obj.quantity if stock_obj else 0

                if qty > available:
                    messages.error(
                        request,
                        f"Transfer quantity ({qty}) for '{prod.name}' exceeds available stock ({available}) in '{transfer.from_warehouse.name}'."
                    )
                    has_error = True

                item_data.append({
                    'product': prod,
                    'available_stock': available,
                    'quantity': qty,
                    'remarks': rem
                })
                total_qty += qty

            if has_error:
                return render(request, 'transfers/transfer_form.html', {
                    'form': form, 'warehouses': warehouses, 'products': products, 'title': 'Create Stock Transfer'
                })

            # Save transfer & items
            transfer.total_products = len(item_data)
            transfer.total_quantity = total_qty
            transfer.save()

            for data in item_data:
                StockTransferItem.objects.create(
                    transfer=transfer,
                    product=data['product'],
                    available_stock_snapshot=data['available_stock'],
                    requested_quantity=data['quantity'],
                    transferred_quantity=data['quantity'],
                    remarks=data['remarks']
                )

            # Log history
            StockTransferHistory.objects.create(
                transfer=transfer,
                action="Transfer Created",
                user=request.user if request.user.is_authenticated else None,
                notes=f"Created transfer {transfer.transfer_number} with {len(item_data)} items."
            )

            messages.success(request, f"Stock Transfer '{transfer.transfer_number}' created successfully.")
            return redirect('transfer-detail', pk=transfer.id)
    else:
        initial = {
            'transfer_number': f"TRF-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            'transfer_date': date.today().strftime('%Y-%m-%d'),
            'status': 'draft'
        }
        form = StockTransferForm(initial=initial)

    return render(request, 'transfers/transfer_form.html', {
        'form': form, 'warehouses': warehouses, 'products': products, 'title': 'Create Stock Transfer'
    })

def transfer_update(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if transfer.status not in ['draft', 'requested']:
        messages.error(request, f"Transfer '{transfer.transfer_number}' is in status '{transfer.get_status_display()}' and cannot be edited.")
        return redirect('transfer-detail', pk=transfer.id)

    warehouses = Warehouse.objects.filter(status='active')
    products = Product.objects.filter(status='active').select_related('unit')

    if request.method == 'POST':
        form = StockTransferForm(request.POST, instance=transfer)
        if form.is_valid():
            transfer = form.save()

            # Replace items
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            remarks_list = request.POST.getlist('remarks[]')

            transfer.items.all().delete()
            total_qty = 0

            for i in range(len(product_ids)):
                try:
                    p_id = int(product_ids[i])
                    qty = int(quantities[i])
                    rem = remarks_list[i] if i < len(remarks_list) else ""
                except (ValueError, IndexError):
                    continue

                if qty <= 0:
                    continue

                prod = Product.objects.filter(pk=p_id).first()
                if prod:
                    stock_obj = WarehouseStock.objects.filter(product=prod, warehouse=transfer.from_warehouse).first()
                    avail = stock_obj.quantity if stock_obj else 0

                    StockTransferItem.objects.create(
                        transfer=transfer,
                        product=prod,
                        available_stock_snapshot=avail,
                        requested_quantity=qty,
                        transferred_quantity=qty,
                        remarks=rem
                    )
                    total_qty += qty

            transfer.total_products = transfer.items.count()
            transfer.total_quantity = total_qty
            transfer.save()

            StockTransferHistory.objects.create(
                transfer=transfer,
                action="Transfer Updated",
                user=request.user if request.user.is_authenticated else None,
                notes="Updated transfer details and item quantities."
            )

            messages.success(request, f"Transfer '{transfer.transfer_number}' updated successfully.")
            return redirect('transfer-detail', pk=transfer.id)
    else:
        form = StockTransferForm(instance=transfer)

    return render(request, 'transfers/transfer_form.html', {
        'form': form, 'warehouses': warehouses, 'products': products, 'transfer': transfer, 'title': f"Edit Transfer {transfer.transfer_number}"
    })

def transfer_approve(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if transfer.status in ['draft', 'requested']:
        transfer.status = 'approved'
        transfer.approved_by = request.user if request.user.is_authenticated else None
        transfer.save()

        StockTransferHistory.objects.create(
            transfer=transfer,
            action="Transfer Approved",
            user=request.user if request.user.is_authenticated else None,
            notes="Transfer request was approved."
        )
        messages.success(request, f"Transfer '{transfer.transfer_number}' has been approved.")
    else:
        messages.warning(request, "Transfer cannot be approved in its current status.")
    return redirect('transfer-detail', pk=transfer.id)

def transfer_start_transit(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if transfer.status in ['approved', 'requested']:
        transfer.status = 'in_transit'
        transfer.save()

        StockTransferHistory.objects.create(
            transfer=transfer,
            action="Transfer Started Transit",
            user=request.user if request.user.is_authenticated else None,
            notes="Goods dispatched and marked as In Transit."
        )
        messages.success(request, f"Transfer '{transfer.transfer_number}' marked as In Transit.")
    return redirect('transfer-detail', pk=transfer.id)

def transfer_receive(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if request.method == 'POST':
        if transfer.status in ['received', 'cancelled', 'rejected']:
            messages.error(request, "Transfer is already finalized and cannot be received again.")
            return redirect('transfer-detail', pk=transfer.id)

        item_ids = request.POST.getlist('item_id[]')
        received_qtys = request.POST.getlist('received_qty[]')

        total_received = 0
        total_transferred = 0

        for i in range(len(item_ids)):
            try:
                item_obj_id = int(item_ids[i])
                rec_qty = int(received_qtys[i])
            except (ValueError, IndexError):
                continue

            item = StockTransferItem.objects.filter(pk=item_obj_id, transfer=transfer).first()
            if not item:
                continue

            item.received_quantity = rec_qty
            item.save()

            total_received += rec_qty
            total_transferred += item.transferred_quantity

            # Update WarehouseStock for Source (Deduct)
            src_stock, _ = WarehouseStock.objects.get_or_create(
                product=item.product,
                warehouse=transfer.from_warehouse,
                defaults={'quantity': 0}
            )
            prev_src = src_stock.quantity
            src_stock.quantity = max(src_stock.quantity - rec_qty, 0)
            src_stock.save()

            # Update WarehouseStock for Destination (Add)
            dest_stock, _ = WarehouseStock.objects.get_or_create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                defaults={'quantity': 0}
            )
            prev_dest = dest_stock.quantity
            dest_stock.quantity += rec_qty
            dest_stock.save()

            # Recalculate combined product total current_stock
            update_product_total_stock(item.product)

            # Record StockMovement logs
            StockMovement.objects.create(
                product=item.product,
                warehouse=transfer.from_warehouse,
                transaction_type='transfer_out',
                quantity=-rec_qty,
                previous_stock=prev_src,
                new_stock=src_stock.quantity,
                unit_cost=item.product.purchase_price or 0.00,
                reference_number=transfer.transfer_number,
                reason=f"Transfer Out to {transfer.to_warehouse.name}",
                user=request.user if request.user.is_authenticated else None
            )

            StockMovement.objects.create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                transaction_type='transfer_in',
                quantity=rec_qty,
                previous_stock=prev_dest,
                new_stock=dest_stock.quantity,
                unit_cost=item.product.purchase_price or 0.00,
                reference_number=transfer.transfer_number,
                reason=f"Transfer In from {transfer.from_warehouse.name}",
                user=request.user if request.user.is_authenticated else None
            )

        # Update Transfer status
        if total_received >= total_transferred:
            transfer.status = 'received'
            action_desc = "Transfer Received"
        else:
            transfer.status = 'partially_received'
            action_desc = "Transfer Partially Received"

        transfer.received_by = request.user if request.user.is_authenticated else None
        transfer.save()

        StockTransferHistory.objects.create(
            transfer=transfer,
            action=action_desc,
            user=request.user if request.user.is_authenticated else None,
            notes=f"Received {total_received} of {total_transferred} total units."
        )

        messages.success(request, f"Transfer '{transfer.transfer_number}' successfully processed ({transfer.get_status_display()}).")
    return redirect('transfer-detail', pk=transfer.id)

def transfer_reject(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if request.method == 'POST':
        form = StockTransferRejectForm(request.POST)
        if form.is_valid():
            transfer.status = 'rejected'
            transfer.rejection_reason = form.cleaned_data['rejection_reason']
            transfer.save()

            StockTransferHistory.objects.create(
                transfer=transfer,
                action="Transfer Rejected",
                user=request.user if request.user.is_authenticated else None,
                notes=f"Reason: {transfer.rejection_reason}"
            )
            messages.warning(request, f"Transfer '{transfer.transfer_number}' was rejected.")
    return redirect('transfer-detail', pk=transfer.id)

def transfer_cancel(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if transfer.status in ['draft', 'requested', 'approved']:
        transfer.status = 'cancelled'
        transfer.save()

        StockTransferHistory.objects.create(
            transfer=transfer,
            action="Transfer Cancelled",
            user=request.user if request.user.is_authenticated else None,
            notes="Transfer was cancelled."
        )
        messages.info(request, f"Transfer '{transfer.transfer_number}' cancelled successfully.")
    else:
        messages.error(request, "Completed or in-transit transfers cannot be directly cancelled.")
    return redirect('transfer-detail', pk=transfer.id)

def transfer_print(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    return render(request, 'transfers/transfer_print.html', {
        'transfer': transfer,
        'items': transfer.items.select_related('product', 'product__unit').all()
    })

def export_transfers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_transfers.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Transfer Number', 'Date', 'From Warehouse', 'To Warehouse', 'Priority',
        'Total Products', 'Total Quantity', 'Status', 'Requested By', 'Received By', 'Created At'
    ])

    transfers = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse', 'requested_by', 'received_by').all()
    for t in transfers:
        writer.writerow([
            t.transfer_number,
            t.transfer_date.strftime('%Y-%m-%d'),
            t.from_warehouse.name,
            t.to_warehouse.name,
            t.get_priority_display(),
            t.total_products,
            t.total_quantity,
            t.get_status_display(),
            t.requested_by.username if t.requested_by else 'N/A',
            t.received_by.username if t.received_by else 'N/A',
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else ''
        ])

    return response
