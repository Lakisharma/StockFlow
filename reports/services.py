from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField
from django.utils import timezone

from categories.models import Category
from brands.models import Brand
from products.models import Product, Warehouse, WarehouseStock
from suppliers.models import Supplier
from purchases.models import Purchase, PurchaseItem
from inventory.models import StockMovement
from transfers.models import StockTransfer, StockTransferItem

class ReportAnalyticsService:

    @staticmethod
    def parse_date_range(range_type, custom_start=None, custom_end=None):
        today = date.today()
        if range_type == 'today':
            return today, today
        elif range_type == 'yesterday':
            yest = today - timedelta(days=1)
            return yest, yest
        elif range_type == 'this_week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif range_type == 'this_month':
            start = date(today.year, today.month, 1)
            return start, today
        elif range_type == 'last_month':
            first_this_month = date(today.year, today.month, 1)
            last_day_last_month = first_this_month - timedelta(days=1)
            first_day_last_month = date(last_day_last_month.year, last_day_last_month.month, 1)
            return first_day_last_month, last_day_last_month
        elif range_type == 'this_year':
            start = date(today.year, 1, 1)
            return start, today
        elif range_type == 'custom' and custom_start and custom_end:
            try:
                s = date.fromisoformat(custom_start)
                e = date.fromisoformat(custom_end)
                return s, e
            except ValueError:
                pass
        return None, None  # All time

    @classmethod
    def get_dashboard_metrics(cls, start_date=None, end_date=None):
        purchases_qs = Purchase.objects.all()
        if start_date and end_date:
            purchases_qs = purchases_qs.filter(purchase_date__range=(start_date, end_date))

        stocks = WarehouseStock.objects.select_related('product').all()
        total_inv_qty = sum(s.quantity for s in stocks)
        total_inv_val = sum(s.inventory_value for s in stocks)

        low_stock_count = sum(1 for s in stocks if 0 < s.quantity <= s.min_stock_level)
        out_stock_count = sum(1 for s in stocks if s.quantity == 0)

        total_purchases = purchases_qs.count()
        total_purchase_amt = purchases_qs.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')

        return {
            'total_products': Product.objects.count(),
            'total_inventory_qty': total_inv_qty,
            'total_inventory_value': total_inv_val,
            'total_purchases': total_purchases,
            'total_purchase_amount': total_purchase_amt,
            'total_suppliers': Supplier.objects.count(),
            'total_warehouses': Warehouse.objects.count(),
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_stock_count,
        }

    @classmethod
    def get_inventory_report_data(cls, warehouse_id=None, category_id=None, brand_id=None):
        qs = WarehouseStock.objects.select_related('product', 'product__category', 'product__brand', 'product__unit', 'warehouse').all()
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        if category_id:
            qs = qs.filter(product__category_id=category_id)
        if brand_id:
            qs = qs.filter(product__brand_id=brand_id)
        return qs

    @classmethod
    def get_stock_movement_report_data(cls, start_date=None, end_date=None, transaction_type=None, warehouse_id=None):
        qs = StockMovement.objects.select_related('product', 'warehouse', 'user').all()
        if start_date and end_date:
            qs = qs.filter(created_at__date__range=(start_date, end_date))
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs

    @classmethod
    def get_purchase_report_data(cls, start_date=None, end_date=None, supplier_id=None, warehouse_id=None):
        qs = Purchase.objects.select_related('supplier', 'warehouse').all()
        if start_date and end_date:
            qs = qs.filter(purchase_date__range=(start_date, end_date))
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs

    @classmethod
    def get_supplier_report_data(cls):
        suppliers = Supplier.objects.annotate(
            total_purchase_count=Count('purchases'),
            total_purchase_amount=Sum('purchases__grand_total'),
            total_paid_amount=Sum('purchases__paid_amount'),
            total_pending_amount=Sum('purchases__pending_amount')
        ).all()
        return suppliers

    @classmethod
    def get_warehouse_report_data(cls):
        warehouses = Warehouse.objects.all()
        data = []
        for wh in warehouses:
            stocks = WarehouseStock.objects.filter(warehouse=wh)
            total_qty = sum(s.quantity for s in stocks)
            total_val = sum(s.inventory_value for s in stocks)
            low_stock = sum(1 for s in stocks if 0 < s.quantity <= s.min_stock_level)
            out_stock = sum(1 for s in stocks if s.quantity == 0)

            data.append({
                'warehouse': wh,
                'total_products': stocks.count(),
                'total_quantity': total_qty,
                'inventory_value': total_val,
                'low_stock_count': low_stock,
                'out_of_stock_count': out_stock,
            })
        return data

    @classmethod
    def get_low_stock_report_data(cls, warehouse_id=None):
        qs = WarehouseStock.objects.select_related('product', 'product__unit', 'warehouse').all()
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        # Filter low stock
        low_stocks = [s for s in qs if 0 < s.quantity <= s.min_stock_level]
        return low_stocks

    @classmethod
    def get_out_of_stock_report_data(cls, warehouse_id=None):
        qs = WarehouseStock.objects.select_related('product', 'product__category', 'product__brand', 'warehouse').all()
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        out_stocks = [s for s in qs if s.quantity == 0]
        return out_stocks

    @classmethod
    def get_gst_report_data(cls, start_date=None, end_date=None):
        qs = Purchase.objects.select_related('supplier').all()
        if start_date and end_date:
            qs = qs.filter(purchase_date__range=(start_date, end_date))

        total_taxable = sum(p.subtotal for p in qs)
        total_gst = sum(p.tax_amount for p in qs)
        total_cgst = total_gst * Decimal('0.5')
        total_sgst = total_gst * Decimal('0.5')
        total_grand = sum(p.grand_total for p in qs)

        return {
            'purchases': qs,
            'summary': {
                'total_taxable': total_taxable,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_igst': Decimal('0.00'),
                'total_gst': total_gst,
                'total_grand': total_grand,
            }
        }

    @classmethod
    def get_valuation_report_data(cls):
        stocks = WarehouseStock.objects.select_related('product', 'warehouse', 'product__category').all()
        total_val = sum(s.inventory_value for s in stocks)

        # Warehouse breakdown
        wh_breakdown = {}
        for s in stocks:
            wh_name = s.warehouse.name
            wh_breakdown[wh_name] = wh_breakdown.get(wh_name, Decimal('0.00')) + s.inventory_value

        # Category breakdown
        cat_breakdown = {}
        for s in stocks:
            cat_name = s.product.category.name if s.product.category else 'Uncategorized'
            cat_breakdown[cat_name] = cat_breakdown.get(cat_name, Decimal('0.00')) + s.inventory_value

        return {
            'stocks': stocks,
            'total_valuation': total_val,
            'warehouse_breakdown': wh_breakdown,
            'category_breakdown': cat_breakdown,
        }

    @classmethod
    def get_warehouse_comparison(cls, wh1_id, wh2_id):
        wh1 = Warehouse.objects.filter(pk=wh1_id).first()
        wh2 = Warehouse.objects.filter(pk=wh2_id).first()

        if not wh1 or not wh2:
            return None

        stocks1 = WarehouseStock.objects.filter(warehouse=wh1)
        stocks2 = WarehouseStock.objects.filter(warehouse=wh2)

        return {
            'wh1': {
                'name': wh1.name,
                'code': wh1.code,
                'total_products': stocks1.count(),
                'total_qty': sum(s.quantity for s in stocks1),
                'valuation': sum(s.inventory_value for s in stocks1),
                'low_stock': sum(1 for s in stocks1 if 0 < s.quantity <= s.min_stock_level),
                'out_stock': sum(1 for s in stocks1 if s.quantity == 0),
            },
            'wh2': {
                'name': wh2.name,
                'code': wh2.code,
                'total_products': stocks2.count(),
                'total_qty': sum(s.quantity for s in stocks2),
                'valuation': sum(s.inventory_value for s in stocks2),
                'low_stock': sum(1 for s in stocks2 if 0 < s.quantity <= s.min_stock_level),
                'out_stock': sum(1 for s in stocks2 if s.quantity == 0),
            }
        }
