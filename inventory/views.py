from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from products.models import Product, Warehouse, WarehouseStock
from inventory.models import StockMovement
from inventory.services import InventoryLedgerService

def update_product_total_stock(product):
    total_prod_stock = sum(ws.quantity for ws in WarehouseStock.objects.filter(product=product))
    product.stock_quantity = total_prod_stock
    product.save()
    return total_prod_stock

class UnifiedStockLedgerView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        movements = StockMovement.objects.select_related('product', 'warehouse', 'batch', 'serial', 'user').all()[:100]
        products = Product.objects.all()
        warehouses = Warehouse.objects.all()

        context = {
            'movements': movements,
            'products': products,
            'warehouses': warehouses,
            'active_menu': 'inventory_ledger'
        }
        return render(request, 'inventory/stock_ledger.html', context)

class StockBalanceSummaryView(View):
    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return redirect('login')

        products = Product.objects.filter(pk=pk) if pk else Product.objects.all()
        balances_data = []

        for prod in products:
            bal = InventoryLedgerService.get_stock_balances(prod)
            balances_data.append({
                'product': prod,
                'balances': bal
            })

        context = {
            'balances_data': balances_data,
            'active_menu': 'stock_balances'
        }
        return render(request, 'inventory/stock_balances.html', context)

class WorkflowStatusCenterView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        return render(request, 'inventory/workflow_status.html', {'active_menu': 'workflow_status'})
