from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
from products.models import WarehouseStock
from inventory.models import StockMovement
from batches.services import BatchService
from notifications.services import NotificationService
from users.services import RBACService
from .models import PurchaseOrder, GoodsReceiptNote, GRNItem

class ProcurementService:

    @classmethod
    def generate_po_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = PurchaseOrder.objects.count() + 1
        while True:
            candidate = f"PO-{year_str}-{count:04d}"
            if not PurchaseOrder.objects.filter(po_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def generate_grn_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = GoodsReceiptNote.objects.count() + 1
        while True:
            candidate = f"GRN-{year_str}-{count:04d}"
            if not GoodsReceiptNote.objects.filter(grn_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def submit_po_for_approval(cls, po, user):
        po.status = 'pending_approval'
        po.save()

        NotificationService.notify_role_or_all(
            role_name='Super Admin',
            title=f"PO Awaiting Approval: {po.po_number}",
            message=f"Purchase Order '{po.po_number}' ({po.supplier.name}) submitted by {user.username} is pending approval.",
            notification_type='purchase',
            priority='high',
            module='Purchases',
            action_url=f"/purchases/orders/{po.id}/",
            record_type='PurchaseOrder',
            record_id=po.id
        )
        return True

    @classmethod
    def approve_po(cls, po, user, notes=""):
        po.status = 'approved'
        po.approved_by = user
        po.approval_notes = notes
        po.save()

        NotificationService.notify_user(
            user=po.created_by or user,
            title=f"PO Approved: {po.po_number}",
            message=f"Purchase Order '{po.po_number}' has been approved.",
            notification_type='purchase',
            priority='normal',
            module='Purchases',
            action_url=f"/purchases/orders/{po.id}/",
            record_type='PurchaseOrder',
            record_id=po.id
        )
        return True

    @classmethod
    def reject_po(cls, po, user, notes=""):
        po.status = 'rejected'
        po.approval_notes = notes
        po.save()

        NotificationService.notify_user(
            user=po.created_by or user,
            title=f"PO Rejected: {po.po_number}",
            message=f"Purchase Order '{po.po_number}' was rejected. Reason: {notes}",
            notification_type='purchase',
            priority='high',
            module='Purchases',
            action_url=f"/purchases/orders/{po.id}/",
            record_type='PurchaseOrder',
            record_id=po.id
        )
        return True

    @classmethod
    @transaction.atomic
    def confirm_grn(cls, grn, user):
        """Atomically updates warehouse stock, batch, serials, PO status, audit trail, and notifications upon GRN confirmation."""
        if grn.status == 'confirmed':
            return True

        for item in grn.items.all():
            qty_accepted = item.accepted_quantity
            if qty_accepted <= 0:
                continue

            ws, _ = WarehouseStock.objects.get_or_create(product=item.product, warehouse=grn.warehouse)
            prev_stock = ws.quantity

            # Create or update ProductBatch if tracked
            b_num = item.batch_number or (f"BATCH-{grn.grn_number}" if (item.product.has_batch_tracking or item.product.require_batch_no) else None)
            
            if b_num:
                batch = BatchService.create_or_update_batch(
                    product=item.product,
                    warehouse=grn.warehouse,
                    batch_number=b_num,
                    quantity=qty_accepted,
                    expiry_date=item.expiry_date,
                    mfg_date=item.mfg_date,
                    supplier=grn.supplier,
                    purchase_invoice=grn.invoice_number or grn.grn_number,
                    purchase_price=item.rate
                )
            else:
                batch = None
                ws.quantity += qty_accepted
                ws.save()
                item.product.current_stock = sum(w.quantity for w in WarehouseStock.objects.filter(product=item.product))
                item.product.save()

            ws.refresh_from_db()

            # Record Stock Movement
            StockMovement.objects.create(
                product=item.product,
                warehouse=grn.warehouse,
                transaction_type='purchase',
                quantity=qty_accepted,
                previous_stock=prev_stock,
                new_stock=ws.quantity,
                unit_cost=item.rate,
                reference_number=grn.grn_number,
                reason=f"Goods Received via GRN {grn.grn_number}",
                user=user
            )

            # Register Serial Numbers if present
            if item.serial_numbers and isinstance(item.serial_numbers, list):
                BatchService.register_serial_numbers(
                    product=item.product,
                    serial_list=item.serial_numbers,
                    batch=batch,
                    warehouse=grn.warehouse,
                    supplier=grn.supplier,
                    purchase_invoice=grn.invoice_number or grn.grn_number
                )

        # Mark GRN Confirmed
        grn.status = 'confirmed'
        grn.confirmed_at = timezone.now()
        grn.save()

        # Update Parent PO Status if linked
        if grn.purchase_order:
            po = grn.purchase_order
            total_ordered = sum(pi.quantity for pi in po.items.all())
            total_received_accepted = GRNItem.objects.filter(grn__purchase_order=po, grn__status='confirmed').aggregate(total=models.Sum('accepted_quantity'))['total'] or 0

            if total_received_accepted >= total_ordered:
                po.status = 'received'
            elif total_received_accepted > 0:
                po.status = 'partially_received'
            po.save()

        # Log Activity & Send Notification
        RBACService.log_activity(user, f"Confirmed GRN '{grn.grn_number}' for PO '{grn.purchase_order.po_number if grn.purchase_order else 'N/A'}'", "Procurement", reference=grn.grn_number)

        NotificationService.notify_user(
            user=user,
            title=f"GRN Confirmed: {grn.grn_number}",
            message=f"Goods Receipt Note '{grn.grn_number}' confirmed. Inventory updated for '{grn.warehouse.name}'.",
            notification_type='purchase',
            priority='normal',
            module='Purchases',
            action_url=f"/purchases/grn/{grn.id}/",
            record_type='GoodsReceiptNote',
            record_id=grn.id
        )
        return True
