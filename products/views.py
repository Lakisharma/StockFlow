import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q, F
from django.http import HttpResponse
from django.contrib import messages
from .models import Product, Warehouse, ProductHistory, WarehouseStock, WarehouseHistory
from .forms import ProductForm
from .warehouse_forms import WarehouseForm
from categories.models import Category
from brands.models import Brand
from units.models import Unit

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query)
            )
            
        # Category Filter
        cat_id = self.request.GET.get('category')
        if cat_id and cat_id != 'all':
            queryset = queryset.filter(category_id=cat_id)
            
        # Brand Filter
        brand_id = self.request.GET.get('brand')
        if brand_id and brand_id != 'all':
            queryset = queryset.filter(brand_id=brand_id)
            
        # Unit Filter
        unit_id = self.request.GET.get('unit')
        if unit_id and unit_id != 'all':
            queryset = queryset.filter(unit_id=unit_id)
            
        # Status Filter
        status = self.request.GET.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        # Stock Status Filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'out_of_stock':
            queryset = queryset.filter(current_stock__lte=0)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(current_stock__gt=0, current_stock__lte=F('min_stock_level'))
        elif stock_status == 'in_stock':
            queryset = queryset.filter(current_stock__gt=F('min_stock_level'))
            
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['name', '-name', 'sku', '-sku', 'selling_price', '-selling_price', 'current_stock', '-current_stock', 'created_at', '-created_at']
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'products'
        
        # Meta contexts for filters
        context['categories'] = Category.objects.filter(status='active')
        context['brands'] = Brand.objects.filter(status='active')
        context['units'] = Unit.objects.filter(status='active')
        
        # Current filter states
        context['q'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', 'all')
        context['selected_brand'] = self.request.GET.get('brand', 'all')
        context['selected_unit'] = self.request.GET.get('unit', 'all')
        context['selected_status'] = self.request.GET.get('status', 'all')
        context['selected_stock_status'] = self.request.GET.get('stock_status', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export triggers
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_products(export_format)
        return super().get(request, *args, **kwargs)

    def export_products(self, format):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"products_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Product Name', 'SKU', 'Barcode', 'Category', 'Brand', 'Unit', 
            'Purchase Price', 'Selling Price', 'MRP', 'Discount', 'GST %', 'Tax Type',
            'Current Stock', 'Stock Status', 'Warehouse', 'Manufacturer', 'Country'
        ])
        
        for prod in queryset:
            brand_name = prod.brand.name if prod.brand else '-'
            warehouse_name = prod.warehouse.name if prod.warehouse else '-'
            writer.writerow([
                prod.name,
                prod.sku,
                prod.barcode,
                prod.category.name,
                brand_name,
                prod.unit.name,
                prod.purchase_price,
                prod.selling_price,
                prod.mrp,
                prod.discount,
                prod.gst_rate,
                prod.tax_type.capitalize(),
                prod.current_stock,
                prod.stock_status,
                warehouse_name,
                prod.manufacturer,
                prod.country_of_origin
            ])
            
        return response

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'products'
        # Get history logs
        context['history_logs'] = self.object.histories.all()[:15]
        return context

class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product '%(name)s' was created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'products'
        context['title'] = "Add New Product"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        ProductHistory.objects.create(
            product=self.object,
            action="created",
            detail=f"Product '{self.object.name}' was created with SKU '{self.object.sku}' and opening stock of {self.object.opening_stock} units."
        )
        return response

class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product '%(name)s' was updated successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'products'
        context['title'] = f"Edit Product: {self.object.name}"
        return context

    def form_valid(self, form):
        old_product = Product.objects.get(pk=self.kwargs['pk'])
        old_price = old_product.selling_price
        old_stock = old_product.current_stock
        
        response = super().form_valid(form)
        
        details = []
        if old_price != self.object.selling_price:
            details.append(f"Price changed from {old_price} to {self.object.selling_price}")
            ProductHistory.objects.create(
                product=self.object,
                action="price_changed",
                detail=f"Selling price adjusted from {old_price} to {self.object.selling_price}."
            )
        if old_stock != self.object.current_stock:
            details.append(f"Stock adjusted from {old_stock} to {self.object.current_stock}")
            ProductHistory.objects.create(
                product=self.object,
                action="stock_updated",
                detail=f"Current stock count adjusted from {old_stock} to {self.object.current_stock}."
            )
            
        ProductHistory.objects.create(
            product=self.object,
            action="updated",
            detail=f"Product details updated. Changes: {', '.join(details) if details else 'None'}"
        )
        return response

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        # Deactivate / safe delete check:
        # Instead of hard delete, we support soft-delete/deactivation.
        # If the user posts 'deactivate_only' or if references might exist:
        deactivate_only = request.POST.get('deactivate_only') == 'true'
        
        if deactivate_only:
            product.status = 'inactive'
            product.save()
            ProductHistory.objects.create(
                product=product,
                action="updated",
                detail="Product status deactivated for safety."
            )
            messages.success(request, f"Product '{product.name}' was deactivated successfully.")
            return redirect('product-list')
            
        messages.success(request, f"Product '{product.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def product_bulk_action(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('ids')
        action = request.POST.get('action')
        
        if product_ids:
            products = Product.objects.filter(id__in=product_ids)
            if action == 'delete':
                count = products.delete()[0]
                messages.success(request, f"Successfully deleted {count} products.")
            elif action == 'deactivate':
                count = products.update(status='inactive')
                messages.success(request, f"Successfully deactivated {count} products.")
            elif action == 'activate':
                count = products.update(status='active')
                messages.success(request, f"Successfully activated {count} products.")
        else:
            messages.warning(request, "No products selected.")
            
    return redirect('product-list')


# ==========================================
# WAREHOUSE MANAGEMENT CBVS
# ==========================================

class WarehouseListView(ListView):
    model = Warehouse
    template_name = 'warehouses/warehouse_list.html'
    context_object_name = 'warehouses'
    paginate_by = 10

    def get_queryset(self):
        queryset = Warehouse.objects.all()

        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(manager_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(city__icontains=query)
            )

        # Status Filter
        status = self.request.GET.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)

        # Type Filter
        w_type = self.request.GET.get('warehouse_type')
        if w_type and w_type != 'all':
            queryset = queryset.filter(warehouse_type=w_type)

        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['name', '-name', 'code', '-code', 'warehouse_type', '-warehouse_type', 'created_at', '-created_at']
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'warehouses'

        # Current filters
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', 'all')
        context['selected_type'] = self.request.GET.get('warehouse_type', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        
        # Calculate dynamic counts for each warehouse
        warehouses_list = context['warehouses']
        for wh in warehouses_list:
            wh.total_products = WarehouseStock.objects.filter(warehouse=wh).count()
            stocks = WarehouseStock.objects.filter(warehouse=wh)
            wh.total_stock = sum(s.quantity for s in stocks)
            
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_warehouses(export_format)
        return super().get(request, *args, **kwargs)

    def export_warehouses(self, format):
        queryset = self.get_queryset()
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"warehouses_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Warehouse Name', 'Warehouse Code', 'Type', 'Manager', 'Phone', 'Email',
            'Address', 'City', 'State', 'Country', 'PIN Code', 'Capacity', 'Capacity Unit', 'Status'
        ])

        for wh in queryset:
            writer.writerow([
                wh.name, wh.code, wh.get_warehouse_type_display(), wh.manager_name, wh.phone, wh.email,
                wh.address, wh.city, wh.state, wh.country, wh.pin_code, wh.total_capacity, wh.capacity_unit, wh.status.capitalize()
            ])
        return response

class WarehouseDetailView(DetailView):
    model = Warehouse
    template_name = 'warehouses/warehouse_detail.html'
    context_object_name = 'warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'warehouses'

        # Warehouse Stocks
        stocks = WarehouseStock.objects.filter(warehouse=self.object)
        context['warehouse_stocks'] = stocks

        # Summary Metrics
        context['total_products'] = stocks.count()
        context['total_stock_qty'] = sum(s.quantity for s in stocks)
        
        # Inventory value (simulated by product price * stock quantity)
        context['inventory_value'] = sum(s.quantity * float(s.product.selling_price) for s in stocks)
        
        # Alerts
        context['low_stock_items'] = sum(1 for s in stocks if s.stock_status == 'Low Stock')
        context['out_of_stock_items'] = sum(1 for s in stocks if s.stock_status == 'Out of Stock')

        # Capacity Utilization
        used = context['total_stock_qty']
        capacity = self.object.total_capacity
        context['used_capacity'] = used
        context['utilization_percentage'] = min(int((used / capacity) * 100), 100) if capacity > 0 else 0
        context['available_capacity'] = max(capacity - used, 0)

        # Recent activities log
        context['history_logs'] = self.object.histories.all()[:15]
        return context

class WarehouseCreateView(SuccessMessageMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'warehouses/warehouse_form.html'
    success_url = reverse_lazy('warehouse-list')
    success_message = "Warehouse '%(name)s' was created successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'warehouses'
        context['title'] = "Add New Warehouse"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        WarehouseHistory.objects.create(
            warehouse=self.object,
            action="created",
            detail=f"Warehouse '{self.object.name}' was created with total capacity of {self.object.total_capacity} {self.object.capacity_unit}."
        )
        return response

class WarehouseUpdateView(SuccessMessageMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'warehouses/warehouse_form.html'
    success_url = reverse_lazy('warehouse-list')
    success_message = "Warehouse '%(name)s' was updated successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'warehouses'
        context['title'] = f"Edit Warehouse: {self.object.name}"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        WarehouseHistory.objects.create(
            warehouse=self.object,
            action="updated",
            detail=f"Warehouse configurations updated."
        )
        return response

class WarehouseDeleteView(DeleteView):
    model = Warehouse
    template_name = 'warehouses/warehouse_confirm_delete.html'
    success_url = reverse_lazy('warehouse-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if warehouse contains any stored items
        stocks_count = WarehouseStock.objects.filter(warehouse=self.object, quantity__gt=0).count()
        context['has_stock'] = stocks_count > 0
        return context

    def post(self, request, *args, **kwargs):
        warehouse = self.get_object()
        stocks_count = WarehouseStock.objects.filter(warehouse=warehouse, quantity__gt=0).count()
        deactivate_only = request.POST.get('deactivate_only') == 'true'

        if stocks_count > 0 or deactivate_only:
            warehouse.status = 'inactive'
            warehouse.save()
            WarehouseHistory.objects.create(
                warehouse=warehouse,
                action="deactivated",
                detail="Warehouse status set to Inactive due to active stock counts."
            )
            messages.success(request, f"Warehouse '{warehouse.name}' contains active stocks and was deactivated successfully.")
            return redirect('warehouse-list')

        messages.success(request, f"Warehouse '{warehouse.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def warehouse_bulk_action(request):
    if request.method == 'POST':
        warehouse_ids = request.POST.getlist('ids')
        action = request.POST.get('action')

        if warehouse_ids:
            warehouses = Warehouse.objects.filter(id__in=warehouse_ids)
            if action == 'delete':
                # Safety check
                for wh in warehouses:
                    stocks_count = WarehouseStock.objects.filter(warehouse=wh, quantity__gt=0).count()
                    if stocks_count > 0:
                        wh.status = 'inactive'
                        wh.save()
                    else:
                        wh.delete()
                messages.success(request, "Successfully processed selected warehouses.")
            elif action == 'deactivate':
                warehouses.update(status='inactive')
                messages.success(request, "Successfully deactivated selected warehouses.")
            elif action == 'activate':
                warehouses.update(status='active')
                messages.success(request, "Successfully activated selected warehouses.")
        else:
            messages.warning(request, "No warehouses selected.")

    return redirect('warehouse-list')
