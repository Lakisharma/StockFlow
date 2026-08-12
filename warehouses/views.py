from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Q
from products.models import Warehouse, Product, WarehouseStock
from employees.models import Employee
from .models import WarehouseZone, WarehouseBin, WarehouseReorderSetting
from .services import WarehouseService

class MultiWarehouseDashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        wh_id = request.GET.get('warehouse')
        warehouses = WarehouseService.get_user_permitted_warehouses(request.user)
        selected_wh = warehouses.filter(pk=wh_id).first() if wh_id else None

        metrics = WarehouseService.get_warehouse_dashboard_metrics(warehouse_id=selected_wh.id if selected_wh else None, user=request.user)

        context = {
            'warehouses': warehouses,
            'selected_warehouse': selected_wh,
            'metrics': metrics,
            'active_menu': 'warehouses'
        }
        return render(request, 'warehouses/dashboard.html', context)

class WarehouseListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = WarehouseService.get_user_permitted_warehouses(request.user)
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search) | Q(city__icontains=search) | Q(manager_name__icontains=search))

        context = {
            'warehouses': qs,
            'search': search,
            'active_menu': 'warehouses'
        }
        return render(request, 'warehouses/warehouse_list.html', context)

class WarehouseDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        wh = get_object_or_404(Warehouse, pk=pk)
        zones = WarehouseZone.objects.filter(warehouse=wh)
        staff = Employee.objects.filter(primary_warehouse=wh)
        stocks = WarehouseStock.objects.select_related('product').filter(warehouse=wh)[:50]

        metrics = WarehouseService.get_warehouse_dashboard_metrics(warehouse_id=wh.id, user=request.user)

        context = {
            'warehouse': wh,
            'zones': zones,
            'staff': staff,
            'stocks': stocks,
            'metrics': metrics,
            'active_menu': 'warehouses'
        }
        return render(request, 'warehouses/warehouse_detail.html', context)

class WarehouseZoneBinListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        zones = WarehouseZone.objects.select_related('warehouse').prefetch_related('bins').all()
        warehouses = WarehouseService.get_user_permitted_warehouses(request.user)

        context = {
            'zones': zones,
            'warehouses': warehouses,
            'active_menu': 'warehouses'
        }
        return render(request, 'warehouses/zones_list.html', context)

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        wh_id = request.POST.get('warehouse')
        code = request.POST.get('zone_code')
        name = request.POST.get('zone_name')
        desc = request.POST.get('description', '')

        wh = get_object_or_404(Warehouse, pk=wh_id)
        zone, created = WarehouseZone.objects.get_or_create(
            warehouse=wh,
            zone_code=code,
            defaults={'zone_name': name, 'description': desc}
        )

        messages.success(request, f"Zone '{zone.zone_name}' ({zone.zone_code}) created for {wh.name}.")
        return redirect('warehouse-zones')

class WarehouseComparisonView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        matrix = WarehouseService.get_warehouse_comparison_data()
        context = {
            'matrix': matrix,
            'active_menu': 'warehouses'
        }
        return render(request, 'warehouses/comparison.html', context)
