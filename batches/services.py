from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from products.models import Product, Warehouse, WarehouseStock
from notifications.services import NotificationService
from users.services import RBACService
from .models import ProductBatch, ProductSerialNumber

class BatchService:

    @classmethod
    def generate_auto_batch_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = ProductBatch.objects.count() + 1
        while True:
            b_no = f"BATCH-{year_str}-{count:04d}"
            if not ProductBatch.objects.filter(batch_number=b_no).exists():
                return b_no
            count += 1

    @classmethod
    @transaction.atomic
    def create_or_update_batch(cls, product, warehouse, batch_number, quantity, expiry_date=None, mfg_date=None, supplier=None, purchase_invoice="", purchase_price=None, selling_price=None):
        if not batch_number:
            batch_number = cls.generate_auto_batch_number()

        batch, created = ProductBatch.objects.get_or_create(
            batch_number=batch_number,
            product=product,
            warehouse=warehouse,
            defaults={
                'supplier': supplier,
                'purchase_invoice': purchase_invoice,
                'mfg_date': mfg_date,
                'expiry_date': expiry_date,
                'initial_quantity': quantity,
                'available_quantity': quantity,
                'purchase_price': purchase_price or product.purchase_price or 0.00,
                'selling_price': selling_price or product.selling_price or 0.00,
            }
        )

        if not created:
            batch.available_quantity += quantity
            batch.initial_quantity += quantity
            if expiry_date:
                batch.expiry_date = expiry_date
            if mfg_date:
                batch.mfg_date = mfg_date
            batch.save()

        # Update WarehouseStock
        ws, _ = WarehouseStock.objects.get_or_create(product=product, warehouse=warehouse)
        ws.quantity = max(ws.quantity + quantity, 0)
        ws.save()

        # Update Product overall stock
        product.current_stock = sum(w.quantity for w in WarehouseStock.objects.filter(product=product))
        product.save()

        return batch

    @classmethod
    def get_fefo_batches(cls, product, warehouse, qty_needed=1):
        """Implements FEFO (First Expiry, First Out) dispatch algorithm."""
        batches = ProductBatch.objects.filter(
            product=product,
            warehouse=warehouse,
            available_quantity__gt=0,
            status__in=['active', 'expiring_soon']
        ).order_by('expiry_date', 'created_at')

        allocations = []
        rem_needed = qty_needed

        for b in batches:
            if rem_needed <= 0:
                break
            take_qty = min(b.available_quantity, rem_needed)
            allocations.append({
                'batch': b,
                'batch_number': b.batch_number,
                'expiry_date': b.expiry_date,
                'take_quantity': take_qty,
                'available_quantity': b.available_quantity
            })
            rem_needed -= take_qty

        return {
            'allocations': allocations,
            'is_fully_allocated': rem_needed <= 0,
            'unallocated_quantity': max(rem_needed, 0)
        }

    @classmethod
    @transaction.atomic
    def register_serial_numbers(cls, product, serial_list, batch=None, warehouse=None, supplier=None, purchase_invoice="", warranty_months=12):
        created_serials = []
        today = timezone.now().date()
        w_end = today + timedelta(days=warranty_months * 30) if warranty_months else None

        for s_num in serial_list:
            s_num = str(s_num).strip()
            if not s_num:
                continue
            if ProductSerialNumber.objects.filter(serial_number=s_num).exists():
                raise ValueError(f"Serial number '{s_num}' already exists in the system!")

            sn = ProductSerialNumber.objects.create(
                serial_number=s_num,
                product=product,
                batch=batch,
                warehouse=warehouse,
                supplier=supplier,
                purchase_invoice=purchase_invoice,
                purchase_date=today,
                warranty_start=today,
                warranty_end=w_end,
                status='in_stock'
            )
            created_serials.append(sn)

        return created_serials

    @classmethod
    def dispatch_expiry_alerts(cls):
        today = timezone.now().date()
        batches = ProductBatch.objects.filter(available_quantity__gt=0, expiry_date__isnull=False)

        alerts_sent = 0
        for b in batches:
            days = (b.expiry_date - today).days
            if days < 0:
                b.status = 'expired'
                b.save()
                title = f"CRITICAL: Batch '{b.batch_number}' EXPIRED"
                priority = 'critical'
                notif_type = 'out_of_stock'
            elif days <= 30:
                b.status = 'expiring_soon'
                b.save()
                title = f"WARNING: Batch '{b.batch_number}' expires in {days} days"
                priority = 'high' if days <= 7 else 'normal'
                notif_type = 'low_stock'
            else:
                continue

            msg = f"Batch '{b.batch_number}' of '{b.product.name}' ({b.available_quantity} units in {b.warehouse.name}) expires on {b.expiry_date}."
            action_url = f"/batches/expiry/expiring-soon/?search={b.batch_number}"

            NotificationService.notify_role_or_all(
                role_name='Warehouse Staff',
                title=title,
                message=msg,
                notification_type=notif_type,
                priority=priority,
                module='Batches & Expiry',
                action_url=action_url,
                record_type='ProductBatch',
                record_id=b.id
            )
            alerts_sent += 1

        return alerts_sent
