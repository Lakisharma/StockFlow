import csv
from datetime import date
from decimal import Decimal
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.db.models import Sum, Count, Q

from categories.models import Category
from brands.models import Brand
from products.models import Product, Warehouse, WarehouseStock
from suppliers.models import Supplier
from purchases.models import Purchase
from inventory.models import StockMovement
from transfers.models import StockTransfer
from .services import ReportAnalyticsService

class ReportDashboardView(View):
    def get(self, request):
        range_type = request.GET.get('range_type', 'this_month')
        c_start = request.GET.get('start_date')
        c_end = request.GET.get('end_date')

        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)
        metrics = ReportAnalyticsService.get_dashboard_metrics(s_date, e_date)

        # Warehouses for comparison
        warehouses = Warehouse.objects.filter(status='active')
        wh1_id = request.GET.get('wh1', warehouses[0].id if warehouses.count() > 0 else None)
        wh2_id = request.GET.get('wh2', warehouses[1].id if warehouses.count() > 1 else wh1_id)

        comparison = None
        if wh1_id and wh2_id:
            comparison = ReportAnalyticsService.get_warehouse_comparison(wh1_id, wh2_id)

        # Category Analytics Breakdown
        categories = Category.objects.all()
        category_analytics = []
        for cat in categories:
            prods = Product.objects.filter(category=cat)
            stocks = WarehouseStock.objects.filter(product__category=cat)
            purchases = Purchase.objects.filter(items__product__category=cat).distinct()

            total_qty = sum(s.quantity for s in stocks)
            inv_val = sum(s.inventory_value for s in stocks)
            purch_val = sum(p.grand_total for p in purchases)

            category_analytics.append({
                'category': cat,
                'product_count': prods.count(),
                'stock_qty': total_qty,
                'inventory_value': inv_val,
                'purchase_value': purch_val
            })

        return render(request, 'reports/reports_dashboard.html', {
            'metrics': metrics,
            'range_type': range_type,
            'start_date': s_date.strftime('%Y-%m-%d') if s_date else '',
            'end_date': e_date.strftime('%Y-%m-%d') if e_date else '',
            'warehouses': warehouses,
            'wh1_selected': int(wh1_id) if wh1_id else '',
            'wh2_selected': int(wh2_id) if wh2_id else '',
            'comparison': comparison,
            'category_analytics': category_analytics
        })

class InventoryReportView(View):
    def get(self, request):
        wh_id = request.GET.get('warehouse')
        cat_id = request.GET.get('category')
        brd_id = request.GET.get('brand')

        stocks = ReportAnalyticsService.get_inventory_report_data(wh_id, cat_id, brd_id)

        return render(request, 'reports/inventory_report.html', {
            'stocks': stocks,
            'warehouses': Warehouse.objects.filter(status='active'),
            'categories': Category.objects.all(),
            'brands': Brand.objects.filter(status='active'),
            'selected_wh': wh_id, 'selected_cat': cat_id, 'selected_brd': brd_id
        })

class StockMovementReportView(View):
    def get(self, request):
        range_type = request.GET.get('range_type', 'this_month')
        c_start = request.GET.get('start_date')
        c_end = request.GET.get('end_date')
        tx_type = request.GET.get('transaction_type')
        wh_id = request.GET.get('warehouse')

        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)
        movements = ReportAnalyticsService.get_stock_movement_report_data(s_date, e_date, tx_type, wh_id)

        return render(request, 'reports/stock_movement_report.html', {
            'movements': movements,
            'warehouses': Warehouse.objects.filter(status='active'),
            'transaction_types': StockMovement.TRANSACTION_TYPE_CHOICES,
            'range_type': range_type, 'selected_tx': tx_type, 'selected_wh': wh_id
        })

class PurchaseReportView(View):
    def get(self, request):
        range_type = request.GET.get('range_type', 'this_month')
        c_start = request.GET.get('start_date')
        c_end = request.GET.get('end_date')
        supp_id = request.GET.get('supplier')
        wh_id = request.GET.get('warehouse')

        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)
        purchases = ReportAnalyticsService.get_purchase_report_data(s_date, e_date, supp_id, wh_id)

        tot_purchases = purchases.count()
        tot_amount = sum(p.grand_total for p in purchases)
        tot_paid = sum(p.paid_amount for p in purchases)
        tot_pending = sum(p.pending_amount for p in purchases)
        tot_gst = sum(p.tax_amount for p in purchases)

        return render(request, 'reports/purchase_report.html', {
            'purchases': purchases,
            'summary': {
                'total_purchases': tot_purchases,
                'total_amount': tot_amount,
                'total_paid': tot_paid,
                'total_pending': tot_pending,
                'total_gst': tot_gst
            },
            'suppliers': Supplier.objects.filter(status='active'),
            'warehouses': Warehouse.objects.filter(status='active'),
            'range_type': range_type, 'selected_supp': supp_id, 'selected_wh': wh_id
        })

class SupplierReportView(View):
    def get(self, request):
        suppliers = ReportAnalyticsService.get_supplier_report_data()

        # Highlights
        top_supplier = max(suppliers, key=lambda s: s.total_purchase_amount or 0) if suppliers else None
        highest_outstanding = max(suppliers, key=lambda s: s.total_pending_amount or 0) if suppliers else None

        return render(request, 'reports/supplier_report.html', {
            'suppliers': suppliers,
            'top_supplier': top_supplier,
            'highest_outstanding': highest_outstanding
        })

class WarehouseReportView(View):
    def get(self, request):
        data = ReportAnalyticsService.get_warehouse_report_data()
        return render(request, 'reports/warehouse_report.html', {'warehouse_data': data})

class LowStockReportView(View):
    def get(self, request):
        wh_id = request.GET.get('warehouse')
        low_stocks = ReportAnalyticsService.get_low_stock_report_data(wh_id)
        return render(request, 'reports/low_stock_report.html', {
            'low_stocks': low_stocks,
            'warehouses': Warehouse.objects.filter(status='active'),
            'selected_wh': wh_id
        })

class OutOfStockReportView(View):
    def get(self, request):
        wh_id = request.GET.get('warehouse')
        out_stocks = ReportAnalyticsService.get_out_of_stock_report_data(wh_id)
        return render(request, 'reports/out_of_stock_report.html', {
            'out_stocks': out_stocks,
            'warehouses': Warehouse.objects.filter(status='active'),
            'selected_wh': wh_id
        })

class ProductReportView(View):
    def get(self, request):
        products = Product.objects.select_related('category', 'brand', 'unit').annotate(
            total_purchased_qty=Sum('purchaseitem__quantity'),
            total_purchased_amt=Sum('purchaseitem__total_amount'),
            warehouse_count=Count('warehouse_stocks', distinct=True)
        ).all()

        return render(request, 'reports/product_report.html', {'products': products})

class StockTransferReportView(View):
    def get(self, request):
        range_type = request.GET.get('range_type', 'this_month')
        c_start = request.GET.get('start_date')
        c_end = request.GET.get('end_date')
        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)

        transfers = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse', 'requested_by', 'received_by').all()
        if s_date and e_date:
            transfers = transfers.filter(transfer_date__range=(s_date, e_date))

        return render(request, 'reports/stock_transfer_report.html', {
            'transfers': transfers,
            'range_type': range_type
        })

class GSTReportView(View):
    def get(self, request):
        range_type = request.GET.get('range_type', 'this_month')
        c_start = request.GET.get('start_date')
        c_end = request.GET.get('end_date')
        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)

        data = ReportAnalyticsService.get_gst_report_data(s_date, e_date)
        return render(request, 'reports/gst_report.html', {
            'purchases': data['purchases'],
            'summary': data['summary'],
            'range_type': range_type
        })

class ValuationReportView(View):
    def get(self, request):
        data = ReportAnalyticsService.get_valuation_report_data()
        return render(request, 'reports/valuation_report.html', {
            'stocks': data['stocks'],
            'total_valuation': data['total_valuation'],
            'warehouse_breakdown': data['warehouse_breakdown'],
            'category_breakdown': data['category_breakdown']
        })

def export_report_csv(request, report_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    writer = csv.writer(response)

    if report_type == 'inventory':
        writer.writerow(['Product', 'SKU', 'Category', 'Brand', 'Warehouse', 'Current Stock', 'Min Stock', 'Price (INR)', 'Value (INR)', 'Status'])
        stocks = ReportAnalyticsService.get_inventory_report_data()
        for s in stocks:
            writer.writerow([s.product.name, s.product.sku, s.product.category.name if s.product.category else '', s.product.brand.name if s.product.brand else '', s.warehouse.name, s.quantity, s.min_stock_level, f"INR {s.product.purchase_price}", f"INR {s.inventory_value}", s.stock_status])

    elif report_type == 'purchase':
        writer.writerow(['Invoice Number', 'Date', 'Supplier', 'Warehouse', 'Subtotal (INR)', 'GST (INR)', 'Grand Total (INR)', 'Payment Status'])
        purchases = ReportAnalyticsService.get_purchase_report_data()
        for p in purchases:
            writer.writerow([p.invoice_number, p.purchase_date.strftime('%Y-%m-%d'), p.supplier.name, p.warehouse.name, f"INR {p.subtotal}", f"INR {p.tax_amount}", f"INR {p.grand_total}", p.get_payment_status_display()])

    elif report_type == 'gst':
        writer.writerow(['Invoice Number', 'Date', 'Supplier', 'GSTIN', 'Taxable Amount (INR)', 'CGST (INR)', 'SGST (INR)', 'Total GST (INR)', 'Grand Total (INR)'])
        data = ReportAnalyticsService.get_gst_report_data()
        for p in data['purchases']:
            cgst = p.tax_amount * Decimal('0.5')
            sgst = p.tax_amount * Decimal('0.5')
            writer.writerow([p.invoice_number, p.purchase_date.strftime('%Y-%m-%d'), p.supplier.name, p.supplier.gstin, f"INR {p.subtotal}", f"INR {cgst}", f"INR {sgst}", f"INR {p.tax_amount}", f"INR {p.grand_total}"])

    else:
        writer.writerow(['Export Record', 'Date'])
        writer.writerow(['Generic Report Export', date.today().strftime('%Y-%m-%d')])

    return response
