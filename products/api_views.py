from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, F
from .models import Product, Warehouse, ProductHistory, WarehouseStock, WarehouseHistory
from .serializers import (
    ProductSerializer, WarehouseSerializer, ProductHistorySerializer, 
    WarehouseStockSerializer, WarehouseHistorySerializer
)

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'manager_name', 'phone', 'city']
    ordering_fields = ['name', 'code', 'warehouse_type', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        status = self.request.query_params.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        warehouse_type = self.request.query_params.get('warehouse_type')
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)
            
        return queryset

    def perform_create(self, serializer):
        warehouse = serializer.save()
        WarehouseHistory.objects.create(
            warehouse=warehouse,
            action="created",
            detail=f"Warehouse '{warehouse.name}' with code '{warehouse.code}' was created."
        )

    def perform_update(self, serializer):
        warehouse = serializer.save()
        WarehouseHistory.objects.create(
            warehouse=warehouse,
            action="updated",
            detail=f"Warehouse details were updated."
        )

class WarehouseStockViewSet(viewsets.ModelViewSet):
    queryset = WarehouseStock.objects.all()
    serializer_class = WarehouseStockSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'warehouse__name']
    ordering_fields = ['quantity', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

class WarehouseHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WarehouseHistory.objects.all()
    serializer_class = WarehouseHistorySerializer
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset

class ProductHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductHistory.objects.all()
    serializer_class = ProductHistorySerializer
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'sku', 'barcode', 'category__name', 'brand__name']
    ordering_fields = ['created_at', 'name', 'sku', 'selling_price', 'current_stock']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Category Filter
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Brand Filter
        brand_id = self.request.query_params.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
            
        # Unit Filter
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
            
        # Status Filter
        status = self.request.query_params.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        # Stock Status Filter
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'out_of_stock':
            queryset = queryset.filter(current_stock__lte=0)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(current_stock__gt=0, current_stock__lte=F('min_stock_level'))
        elif stock_status == 'in_stock':
            queryset = queryset.filter(current_stock__gt=F('min_stock_level'))
            
        return queryset

    def perform_create(self, serializer):
        product = serializer.save()
        ProductHistory.objects.create(
            product=product,
            action="created",
            detail=f"Product '{product.name}' was created with SKU '{product.sku}'."
        )

    def perform_update(self, serializer):
        # Capture old values
        old_product = self.get_object()
        old_price = old_product.selling_price
        old_stock = old_product.current_stock
        
        product = serializer.save()
        
        details = []
        if old_price != product.selling_price:
            details.append(f"Price changed from {old_price} to {product.selling_price}.")
            ProductHistory.objects.create(product=product, action="price_changed", detail=f"Price changed from {old_price} to {product.selling_price}.")
        if old_stock != product.current_stock:
            details.append(f"Stock updated from {old_stock} to {product.current_stock}.")
            ProductHistory.objects.create(product=product, action="stock_updated", detail=f"Stock updated from {old_stock} to {product.current_stock}.")
            
        ProductHistory.objects.create(
            product=product,
            action="updated",
            detail=f"Product profile updated. {'; '.join(details)}"
        )
