from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F
from products.models import Product, Warehouse
from suppliers.models import Supplier
from users.services import RBACService
from .models import ProductBatch, ProductSerialNumber
from .services import BatchService

class BatchListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # Dispatch expiry alerts automatically
        BatchService.dispatch_expiry_alerts()

        qs = ProductBatch.objects.select_related('product', 'warehouse', 'supplier').all()

        search = request.GET.get('search')
        warehouse_id = request.GET.get('warehouse')
        status_filter = request.GET.get('status')

        if search:
            qs = qs.filter(batch_number__icontains=search) | qs.filter(product__name__icontains=search) | qs.filter(product__sku__icontains=search)
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        if status_filter:
            qs = qs.filter(status=status_filter)

        products = Product.objects.all()
        warehouses = RBACService.get_user_warehouses(request.user)
        if warehouses is None:
            warehouses = Warehouse.objects.filter(status='active')
        suppliers = Supplier.objects.all()

        total_batches = ProductBatch.objects.count()
        total_active_stock = ProductBatch.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
        expiring_soon_count = ProductBatch.objects.filter(status='expiring_soon').count()
        expired_count = ProductBatch.objects.filter(status='expired').count()

        context = {
            'batches': qs[:100],
            'products': products,
            'warehouses': warehouses,
            'suppliers': suppliers,
            'search': search,
            'warehouse_filter': warehouse_id,
            'status_filter': status_filter,
            'total_batches': total_batches,
            'total_active_stock': total_active_stock,
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'auto_batch_number': BatchService.generate_auto_batch_number(),
            'active_menu': 'batches'
        }
        return render(request, 'batches/batch_list.html', context)

    def post(self, request):
        product_id = request.POST.get('product')
        warehouse_id = request.POST.get('warehouse')
        supplier_id = request.POST.get('supplier')
        batch_number = request.POST.get('batch_number')
        quantity = int(request.POST.get('quantity', 0))
        mfg_date = request.POST.get('mfg_date') or None
        expiry_date = request.POST.get('expiry_date') or None

        prod = get_object_or_404(Product, pk=product_id)
        wh = get_object_or_404(Warehouse, pk=warehouse_id)
        sup = Supplier.objects.filter(pk=supplier_id).first() if supplier_id else None

        batch = BatchService.create_or_update_batch(
            product=prod,
            warehouse=wh,
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date,
            mfg_date=mfg_date,
            supplier=sup
        )

        messages.success(request, f"Batch '{batch.batch_number}' registered successfully with {quantity} units.")
        return redirect('batch-list')

class ExpiringSoonReportView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        days_preset = int(request.GET.get('days', 30))
        target_date = timezone.now().date() + timedelta(days=days_preset)

        qs = ProductBatch.objects.filter(
            available_quantity__gt=0,
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=target_date
        ).select_related('product', 'warehouse', 'supplier')

        context = {
            'batches': qs,
            'days_preset': days_preset,
            'active_menu': 'batches'
        }
        return render(request, 'batches/expiring_soon.html', context)

class ExpiredStockReportView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = ProductBatch.objects.filter(
            available_quantity__gt=0,
            expiry_date__lt=timezone.now().date()
        ).select_related('product', 'warehouse', 'supplier')

        total_value_loss = sum(b.inventory_value for b in qs)

        context = {
            'batches': qs,
            'total_value_loss': total_value_loss,
            'active_menu': 'batches'
        }
        return render(request, 'batches/expired_stock.html', context)

class SerialNumberListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = ProductSerialNumber.objects.select_related('product', 'batch', 'warehouse', 'supplier').all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(serial_number__icontains=search) | qs.filter(product__name__icontains=search) | qs.filter(product__sku__icontains=search)

        context = {
            'serials': qs[:100],
            'search': search,
            'active_menu': 'batches'
        }
        return render(request, 'batches/serial_list.html', context)

class SerialNumberDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        sn = get_object_or_404(ProductSerialNumber.objects.select_related('product', 'batch', 'warehouse', 'supplier'), pk=pk)
        return render(request, 'batches/serial_detail.html', {'serial': sn, 'active_menu': 'batches'})
