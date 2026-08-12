from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from products.models import Product, Warehouse
from users.services import RBACService
from .models import BarcodeScanHistory, BarcodeLabelPreset
from .services import BarcodeService

class BarcodeScannerView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        warehouses = RBACService.get_user_warehouses(request.user)
        if warehouses is None:
            warehouses = Warehouse.objects.filter(status='active')

        mode = request.GET.get('mode', 'lookup')
        query = request.GET.get('q') or request.GET.get('barcode')

        scan_result = None
        if query:
            scan_result = BarcodeService.lookup_product(query)
            status_val = 'found' if scan_result else 'not_found'
            prod_val = scan_result['product'] if scan_result else None
            BarcodeService.log_scan_history(query, product=prod_val, user=request.user, scan_mode=mode, status=status_val, request=request)

        context = {
            'warehouses': warehouses,
            'mode': mode,
            'query': query,
            'scan_result': scan_result,
            'active_menu': 'barcodes'
        }
        return render(request, 'barcodes/scanner.html', context)

class BarcodeGeneratorView(View):
    def get(self, request, product_id):
        if not request.user.is_authenticated:
            return redirect('login')

        prod = get_object_or_404(Product, pk=product_id)
        if not prod.barcode:
            prod.barcode = BarcodeService.generate_unique_barcode()
            prod.save()

        barcode_svg = BarcodeService.render_barcode_svg(prod.barcode)
        qr_svg = BarcodeService.render_qr_code_svg(prod)

        context = {
            'product': prod,
            'barcode_svg': barcode_svg,
            'qr_svg': qr_svg,
            'active_menu': 'barcodes'
        }
        return render(request, 'barcodes/generator_detail.html', context)

    def post(self, request, product_id):
        if not request.user.is_authenticated:
            return redirect('login')

        prod = get_object_or_404(Product, pk=product_id)
        manual_code = request.POST.get('manual_barcode', '').strip()

        if manual_code:
            existing = Product.objects.filter(barcode=manual_code).exclude(id=prod.id).exists()
            if existing:
                messages.error(request, f"Barcode '{manual_code}' is already assigned to another product!")
            else:
                prod.barcode = manual_code
                prod.save()
                messages.success(request, f"Barcode '{manual_code}' assigned to product successfully.")
        else:
            prod.barcode = BarcodeService.generate_unique_barcode()
            prod.save()
            messages.success(request, f"Unique barcode '{prod.barcode}' generated successfully.")

        return redirect(f'/barcodes/generate/{prod.id}/')

class BarcodeLabelPrintView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        product_id = request.GET.get('product_id')
        preset_size = request.GET.get('size', 'medium')  # small, medium, large
        quantity = int(request.GET.get('quantity', 10))

        products = Product.objects.all()
        selected_product = None
        barcode_svg = None
        qr_svg = None

        if product_id:
            selected_product = Product.objects.filter(id=product_id).first()
        else:
            selected_product = products.first()

        if selected_product:
            if not selected_product.barcode:
                selected_product.barcode = BarcodeService.generate_unique_barcode()
                selected_product.save()

            barcode_svg = BarcodeService.render_barcode_svg(selected_product.barcode)
            qr_svg = BarcodeService.render_qr_code_svg(selected_product)

        context = {
            'products': products,
            'selected_product': selected_product,
            'preset_size': preset_size,
            'quantity': quantity,
            'quantity_range': range(quantity),
            'barcode_svg': barcode_svg,
            'qr_svg': qr_svg,
            'active_menu': 'barcodes'
        }
        return render(request, 'barcodes/label_generator.html', context)

class BarcodeScanHistoryView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        history_qs = BarcodeScanHistory.objects.select_related('product', 'user', 'warehouse').all()[:100]
        return render(request, 'barcodes/scan_history.html', {'history': history_qs, 'active_menu': 'barcodes'})

class MobileWarehouseScannerView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        warehouses = Warehouse.objects.filter(status='active')
        mode = request.GET.get('mode', 'lookup')
        wh_id = request.GET.get('warehouse')
        selected_wh = warehouses.filter(id=wh_id).first() if wh_id else warehouses.first()

        recent_scans = BarcodeScanHistory.objects.select_related('product', 'user', 'warehouse').all()[:20]

        context = {
            'warehouses': warehouses,
            'selected_warehouse': selected_wh,
            'mode': mode,
            'recent_scans': recent_scans,
            'active_menu': 'barcodes'
        }
        return render(request, 'barcodes/mobile_scanner.html', context)

class StockCountingView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        warehouses = Warehouse.objects.filter(status='active')
        wh_id = request.GET.get('warehouse')
        selected_wh = warehouses.filter(id=wh_id).first() if wh_id else warehouses.first()

        from products.models import WarehouseStock
        stocks = WarehouseStock.objects.select_related('product').filter(warehouse=selected_wh) if selected_wh else []

        context = {
            'warehouses': warehouses,
            'selected_warehouse': selected_wh,
            'stocks': stocks,
            'active_menu': 'barcodes'
        }
        return render(request, 'barcodes/stock_counting.html', context)

class ScanSessionsView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        from .models import ScanSession
        sessions = ScanSession.objects.select_related('user', 'warehouse').all()[:50]
        return render(request, 'barcodes/sessions_list.html', {'sessions': sessions, 'active_menu': 'barcodes'})

