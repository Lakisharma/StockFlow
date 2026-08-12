from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from products.models import Product, WarehouseStock
from inventory.models import StockMovement
from batches.models import ProductBatch, ProductSerialNumber
from notifications.services import NotificationService
from users.services import RBACService
from .models import Customer, SalesOrder, SalesOrderItem, PickList, PickListItem, Dispatch, DispatchItem, SalesInvoice

class SalesService:

    @classmethod
    def generate_customer_code(cls):
        count = Customer.objects.count() + 1
        while True:
            candidate = f"CUST-{count:04d}"
            if not Customer.objects.filter(customer_code=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def generate_so_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = SalesOrder.objects.count() + 1
        while True:
            candidate = f"SO-{year_str}-{count:04d}"
            if not SalesOrder.objects.filter(so_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def generate_pick_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = PickList.objects.count() + 1
        while True:
            candidate = f"PICK-{year_str}-{count:04d}"
            if not PickList.objects.filter(pick_list_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def generate_dispatch_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = Dispatch.objects.count() + 1
        while True:
            candidate = f"DISP-{year_str}-{count:04d}"
            if not Dispatch.objects.filter(dispatch_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def generate_invoice_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = SalesInvoice.objects.count() + 1
        while True:
            candidate = f"INV-{year_str}-{count:04d}"
            if not SalesInvoice.objects.filter(invoice_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def submit_so_for_approval(cls, so, user):
        so.status = 'pending_approval'
        so.save()

        NotificationService.notify_role_or_all(
            role_name='Super Admin',
            title=f"Sales Order Awaiting Approval: {so.so_number}",
            message=f"Sales Order '{so.so_number}' for '{so.customer.name}' is pending approval.",
            notification_type='stock_alert',
            priority='high',
            module='Sales',
            action_url=f"/sales/orders/{so.id}/",
            record_type='SalesOrder',
            record_id=so.id
        )
        return True

    @classmethod
    def approve_so(cls, so, user):
        so.status = 'approved'
        so.save()

        NotificationService.notify_user(
            user=so.created_by or user,
            title=f"Sales Order Approved: {so.so_number}",
            message=f"Sales Order '{so.so_number}' has been approved and is ready for picking.",
            notification_type='stock_alert',
            priority='normal',
            module='Sales',
            action_url=f"/sales/orders/{so.id}/",
            record_type='SalesOrder',
            record_id=so.id
        )
        return True

    @classmethod
    @transaction.atomic
    def confirm_dispatch(cls, dispatch, user):
        """Atomically deducts warehouse stock, decrements batch, updates serial numbers to sold, creates invoice, and logs audit trail."""
        if dispatch.status == 'confirmed':
            return True

        for item in dispatch.items.all():
            qty_disp = item.dispatched_quantity
            if qty_disp <= 0:
                continue

            # Update Warehouse Stock
            ws, _ = WarehouseStock.objects.get_or_create(product=item.product, warehouse=dispatch.warehouse)
            prev_stock = ws.quantity
            ws.quantity = max(ws.quantity - qty_disp, 0)
            ws.save()

            # Record Stock Movement
            StockMovement.objects.create(
                product=item.product,
                warehouse=dispatch.warehouse,
                transaction_type='sale',
                quantity=-qty_disp,
                previous_stock=prev_stock,
                new_stock=ws.quantity,
                unit_cost=item.rate,
                reference_number=dispatch.dispatch_number,
                reason=f"Stock Out via Dispatch {dispatch.dispatch_number} for {dispatch.customer.name}",
                user=user
            )

            # Update Product overall stock
            item.product.current_stock = sum(w.quantity for w in WarehouseStock.objects.filter(product=item.product))
            item.product.save()

            # Decrement ProductBatch if batch is specified
            if item.batch_number:
                b = ProductBatch.objects.filter(batch_number=item.batch_number, product=item.product, warehouse=dispatch.warehouse).first()
                if b:
                    b.available_quantity = max(b.available_quantity - qty_disp, 0)
                    if b.available_quantity == 0:
                        b.status = 'exhausted'
                    b.save()

            # Update Serial Numbers status to sold if present
            if item.serial_numbers and isinstance(item.serial_numbers, list):
                ProductSerialNumber.objects.filter(serial_number__in=item.serial_numbers, product=item.product).update(status='sold')

            # Update SO Item dispatched quantity
            item.so_item.dispatched_quantity += qty_disp
            item.so_item.save()

        # Mark Dispatch confirmed
        dispatch.status = 'dispatched'
        dispatch.confirmed_at = timezone.now()
        dispatch.save()

        # Check parent SO fulfillment
        so = dispatch.sales_order
        total_ordered = sum(i.ordered_quantity for i in so.items.all())
        total_dispatched = sum(i.dispatched_quantity for i in so.items.all())

        if total_dispatched >= total_ordered:
            so.status = 'completed'
        elif total_dispatched > 0:
            so.status = 'partially_fulfilled'
        so.save()

        # Auto Generate Sales Invoice
        inv_no = cls.generate_invoice_number()
        invoice = SalesInvoice.objects.create(
            invoice_number=inv_no,
            sales_order=so,
            dispatch=dispatch,
            customer=dispatch.customer,
            warehouse=dispatch.warehouse,
            invoice_date=timezone.now().date(),
            subtotal=so.subtotal,
            discount_amount=so.discount_amount,
            tax_amount=so.tax_amount,
            shipping_charges=so.shipping_charges,
            grand_total=so.grand_total,
            status='issued',
            payment_status='unpaid'
        )

        # Update Customer Outstanding
        dispatch.customer.outstanding_amount = Decimal(str(dispatch.customer.outstanding_amount or 0)) + Decimal(str(so.grand_total or 0))
        dispatch.customer.save()

        # Audit Log & Notification
        RBACService.log_activity(user, f"Confirmed Stock Out Dispatch '{dispatch.dispatch_number}' for Customer '{dispatch.customer.name}'", "Sales", reference=dispatch.dispatch_number)

        NotificationService.notify_user(
            user=user,
            title=f"Dispatch Confirmed: {dispatch.dispatch_number}",
            message=f"Dispatched {total_dispatched} units to '{dispatch.customer.name}'. Invoice '{invoice.invoice_number}' created.",
            notification_type='stock_alert',
            priority='normal',
            module='Sales',
            action_url=f"/sales/dispatches/{dispatch.id}/",
            record_type='Dispatch',
            record_id=dispatch.id
        )
        return True
