from decimal import Decimal
from django.db.models import Sum, Q
from products.models import Warehouse, Product, WarehouseStock
from sales.models import SalesInvoice
from purchases.models import Purchase
from accounting.models import Expense
from transfers.models import StockTransfer
from .models import WarehouseZone, WarehouseBin, WarehouseUserAccess, WarehouseReorderSetting

class WarehouseService:

    @classmethod
    def get_user_permitted_warehouses(cls, user):
        if not user or not user.is_authenticated:
            return Warehouse.objects.none()
        if user.is_superuser or user.is_staff:
            return Warehouse.objects.filter(status='active')
        
        permitted_ids = WarehouseUserAccess.objects.filter(user=user).values_list('warehouse_id', flat=True)
        return Warehouse.objects.filter(id__in=permitted_ids, status='active')

    @classmethod
    def get_warehouse_dashboard_metrics(cls, warehouse_id=None, user=None):
        warehouses_qs = cls.get_user_permitted_warehouses(user)
        if warehouse_id:
            warehouses_qs = warehouses_qs.filter(id=warehouse_id)

        total_warehouses = warehouses_qs.count()
        
        stocks_qs = WarehouseStock.objects.filter(warehouse__in=warehouses_qs)
        total_quantity = stocks_qs.aggregate(total=Sum('quantity'))['total'] or 0

        inventory_value = Decimal('0.00')
        for s in stocks_qs.select_related('product'):
            unit_price = s.product.purchase_price or Decimal('0.00')
            inventory_value += (s.quantity * unit_price)

        total_capacity = warehouses_qs.aggregate(total=Sum('total_capacity'))['total'] or 10000
        capacity_usage_pct = round((total_quantity / total_capacity * 100), 1) if total_capacity > 0 else 0.0

        pending_transfers = StockTransfer.objects.filter(
            Q(from_warehouse__in=warehouses_qs) | Q(to_warehouse__in=warehouses_qs),
            status__in=['pending', 'approved', 'in_transit']
        ).count()

        return {
            'total_warehouses': total_warehouses,
            'total_quantity': total_quantity,
            'inventory_value': inventory_value,
            'total_capacity': total_capacity,
            'capacity_usage_pct': capacity_usage_pct,
            'pending_transfers': pending_transfers,
        }

    @classmethod
    def get_warehouse_comparison_data(cls):
        warehouses = Warehouse.objects.filter(status='active')
        matrix = []

        for w in warehouses:
            stocks = WarehouseStock.objects.filter(warehouse=w)
            stock_qty = stocks.aggregate(total=Sum('quantity'))['total'] or 0
            
            inv_val = Decimal('0.00')
            for s in stocks.select_related('product'):
                inv_val += (s.quantity * (s.product.purchase_price or Decimal('0.00')))

            sales_val = SalesInvoice.objects.filter(warehouse=w, status='paid').aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
            purchases_val = Purchase.objects.filter(warehouse=w, status='paid').aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
            expenses_val = Expense.objects.filter(warehouse=w, status__in=['approved', 'paid']).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            net_profit = sales_val - (purchases_val + expenses_val)

            matrix.append({
                'warehouse': {'id': w.id, 'name': w.name, 'code': w.code, 'city': w.city},
                'stock_qty': stock_qty,
                'inventory_value': inv_val,
                'sales': sales_val,
                'purchases': purchases_val,
                'expenses': expenses_val,
                'net_profit': net_profit,
            })
        return matrix
