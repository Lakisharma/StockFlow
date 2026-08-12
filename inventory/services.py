from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from products.models import Product, Warehouse, WarehouseStock
from inventory.models import StockMovement
from audit_logs.models import SystemAuditLog
from notifications.models import Notification

class InventoryLedgerService:

    @classmethod
    @transaction.atomic
    def record_movement(cls, product, warehouse, transaction_type, quantity, unit_cost=Decimal('0.00'), reference_number='', user=None, batch=None, serial=None, notes='', reason=''):
        stock_obj, _ = WarehouseStock.objects.select_for_update().get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={'quantity': 0, 'min_stock_level': 5, 'max_stock_level': 1000}
        )

        previous_stock = stock_obj.quantity
        new_stock = previous_stock + quantity

        # Update WarehouseStock physical quantity
        stock_obj.quantity = max(new_stock, 0)
        stock_obj.save()

        # Update Product total consolidated stock
        total_prod_stock = sum(ws.quantity for ws in WarehouseStock.objects.filter(product=product))
        product.stock_quantity = total_prod_stock
        product.save()

        # Create immutable StockMovement ledger entry
        movement = StockMovement.objects.create(
            product=product,
            warehouse=warehouse,
            batch=batch,
            serial=serial,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=stock_obj.quantity,
            unit_cost=unit_cost,
            reference_number=reference_number,
            reason=reason,
            notes=notes,
            user=user
        )

        return movement

    @classmethod
    def get_stock_balances(cls, product, warehouse=None):
        from sales.models import SalesOrderItem

        if warehouse:
            ws = WarehouseStock.objects.filter(product=product, warehouse=warehouse).first()
            physical = ws.quantity if ws else 0
            so_items = SalesOrderItem.objects.filter(product=product, sales_order__warehouse=warehouse, sales_order__status__in=['approved', 'confirmed', 'picking'])
        else:
            stocks = WarehouseStock.objects.filter(product=product)
            physical = sum(s.quantity for s in stocks)
            so_items = SalesOrderItem.objects.filter(product=product, sales_order__status__in=['approved', 'confirmed', 'picking'])

        reserved = sum(max(i.ordered_quantity - i.dispatched_quantity, 0) for i in so_items)
        available = max(physical - reserved, 0)

        # Calculate Damaged & Expired
        from stock_adjustments.models import DamagedStockItem
        from batches.models import ProductBatch

        damaged_qs = DamagedStockItem.objects.filter(product=product)
        if warehouse:
            damaged_qs = damaged_qs.filter(warehouse=warehouse)
        damaged = sum(d.quantity for d in damaged_qs)

        today = timezone.now().date()
        expired_qs = ProductBatch.objects.filter(product=product, expiry_date__lt=today)
        if warehouse:
            expired_qs = expired_qs.filter(warehouse=warehouse)
        expired = sum(b.available_quantity for b in expired_qs)

        return {
            'physical_stock': physical,
            'reserved_stock': reserved,
            'available_stock': available,
            'damaged_stock': damaged,
            'expired_stock': expired,
            'in_transit_stock': 0
        }

class SystemIntegrationService:

    @classmethod
    @transaction.atomic
    def execute_purchase_receiving_flow(cls, purchase_order, items_data, user, warehouse):
        from purchases.models import GoodsReceiptNote, GRNItem, Purchase
        from batches.models import ProductBatch, ProductSerialNumber
        from system_admin.services import SystemAdminService

        grn_number = SystemAdminService.get_next_document_number('grn')
        grn = GoodsReceiptNote.objects.create(
            grn_number=grn_number,
            purchase_order=purchase_order,
            warehouse=warehouse,
            supplier=purchase_order.supplier,
            received_date=timezone.now().date(),
            status='confirmed',
            created_by=user
        )

        total_rcvd = 0
        total_amount = Decimal('0.00')

        for item in items_data:
            prod = item['product']
            qty = item['quantity']
            unit_price = item.get('unit_price', prod.purchase_price or Decimal('0.00'))
            line_total = unit_price * qty
            total_amount += line_total
            batch_num = item.get('batch_number')
            expiry_date = item.get('expiry_date')
            serials = item.get('serials', [])

            # Create GRN Line Item
            GRNItem.objects.create(
                grn=grn,
                product=prod,
                ordered_quantity=qty,
                received_quantity=qty,
                accepted_quantity=qty,
                rate=unit_price,
                line_total=line_total
            )

            # Record Batch if provided
            batch_obj = None
            if batch_num and expiry_date:
                batch_obj, _ = ProductBatch.objects.get_or_create(
                    batch_number=batch_num,
                    product=prod,
                    warehouse=warehouse,
                    defaults={'mfg_date': timezone.now().date(), 'expiry_date': expiry_date, 'available_quantity': qty, 'purchase_price': unit_price}
                )

            # Record Serial Numbers if provided
            for sn_val in serials:
                ProductSerialNumber.objects.get_or_create(
                    serial_number=sn_val,
                    product=prod,
                    defaults={'warehouse': warehouse, 'status': 'available'}
                )

            # Add Physical Inventory via Centralized Ledger
            InventoryLedgerService.record_movement(
                product=prod,
                warehouse=warehouse,
                transaction_type='purchase',
                quantity=qty,
                unit_cost=unit_price,
                reference_number=grn.grn_number,
                user=user,
                batch=batch_obj,
                notes=f"Received via GRN {grn.grn_number}"
            )
            total_rcvd += qty

        # Update Purchase Order Status
        purchase_order.status = 'received'
        purchase_order.save()

        # Create Purchase Invoice Entry
        inv_num = SystemAdminService.get_next_document_number('purchase_return')
        invoice = Purchase.objects.create(
            invoice_number=inv_num,
            purchase_order_number=purchase_order.po_number,
            supplier=purchase_order.supplier,
            warehouse=warehouse,
            purchase_date=timezone.now().date(),
            status='received',
            payment_status='pending',
            subtotal=total_amount,
            grand_total=total_amount
        )

        # Audit Log
        from audit_logs.services import AuditLogService
        AuditLogService.log_event(
            user=user,
            action='Purchase Received',
            module='Purchases',
            description=f"GRN {grn.grn_number} created for PO {purchase_order.po_number} ({total_rcvd} items)."
        )

        return grn, invoice

    @classmethod
    @transaction.atomic
    def execute_sales_dispatch_flow(cls, sales_order, items_data, user, warehouse):
        from sales.models import SalesInvoice
        from system_admin.services import SystemAdminService

        total_amount = getattr(sales_order, 'grand_total', Decimal('0.00'))

        # Generate Sales Invoice
        inv_num = SystemAdminService.get_next_document_number('invoice')
        invoice = SalesInvoice.objects.create(
            invoice_number=inv_num,
            sales_order=sales_order,
            customer=sales_order.customer,
            warehouse=warehouse,
            invoice_date=timezone.now().date(),
            subtotal=total_amount,
            grand_total=total_amount,
            status='issued',
            payment_status='unpaid'
        )

        for item in items_data:
            prod = item['product']
            qty = item['quantity']

            # Deduct physical stock via Centralized Ledger
            InventoryLedgerService.record_movement(
                product=prod,
                warehouse=warehouse,
                transaction_type='sales_dispatch',
                quantity=-qty,
                unit_cost=prod.purchase_price or Decimal('0.00'),
                reference_number=invoice.invoice_number,
                user=user,
                notes=f"Dispatched for Invoice {invoice.invoice_number}"
            )

        sales_order.status = 'dispatched'
        sales_order.save()

        from audit_logs.services import AuditLogService
        AuditLogService.log_event(
            user=user,
            action='Sales Dispatched',
            module='Sales',
            description=f"Invoice {invoice.invoice_number} dispatched for SO {sales_order.so_number}."
        )

        return invoice

    @classmethod
    @transaction.atomic
    def execute_sales_return_flow(cls, invoice, items_data, user):
        from sales.models import SalesReturn, SalesReturnItem
        from stock_adjustments.models import DamagedStockItem
        from system_admin.services import SystemAdminService

        return_num = SystemAdminService.get_next_document_number('sales_return')
        sales_return = SalesReturn.objects.create(
            return_number=return_num,
            invoice=invoice,
            customer=invoice.customer,
            warehouse=invoice.warehouse,
            status='approved'
        )

        for item in items_data:
            prod = item['product']
            good_qty = item.get('good_quantity', 0)
            damaged_qty = item.get('damaged_quantity', 0)

            # Good Stock -> Add back to Available Stock
            if good_qty > 0:
                InventoryLedgerService.record_movement(
                    product=prod,
                    warehouse=invoice.warehouse,
                    transaction_type='sales_return',
                    quantity=good_qty,
                    unit_cost=prod.purchase_price or Decimal('0.00'),
                    reference_number=sales_return.return_number,
                    user=user,
                    notes="Good stock returned to inventory"
                )

            # Damaged Stock -> Route to Damaged Stock Item
            if damaged_qty > 0:
                DamagedStockItem.objects.create(
                    product=prod,
                    warehouse=invoice.warehouse,
                    quantity=damaged_qty,
                    reason='Customer Damaged Return',
                    user=user
                )

        return sales_return
