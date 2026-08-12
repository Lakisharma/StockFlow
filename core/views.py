from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import Q

from products.models import Product, Warehouse
from suppliers.models import Supplier
from sales.models import Customer, SalesInvoice
from purchases.models import PurchaseOrder
from batches.models import ProductBatch
from employees.models import Employee

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

class HealthCheckView(View):
    def get(self, request):
        from django.db import connection
        db_healthy = True
        try:
            connection.ensure_connection()
        except Exception:
            db_healthy = False

        status_code = 200 if db_healthy else 503
        return JsonResponse({
            'status': 'healthy' if db_healthy else 'unhealthy',
            'database': 'healthy' if db_healthy else 'unhealthy',
            'storage': 'healthy',
        }, status=status_code)

class GlobalSearchView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        results = []

        # 1. Products
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query)
        )[:5]
        for p in products:
            results.append({
                'category': 'Products',
                'title': p.name,
                'subtitle': f"SKU: {p.sku} | Price: ₹{p.selling_price}",
                'url': f"/products/{p.id}/"
            })

        # 2. Suppliers
        suppliers = Supplier.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(contact_person__icontains=query)
        )[:5]
        for s in suppliers:
            results.append({
                'category': 'Suppliers',
                'title': s.name,
                'subtitle': f"Code: {s.code} | Contact: {s.phone}",
                'url': f"/suppliers/{s.id}/edit/"
            })

        # 3. Customers
        customers = Customer.objects.filter(
            Q(name__icontains=query) | Q(customer_code__icontains=query) | Q(phone__icontains=query)
        )[:5]
        for c in customers:
            results.append({
                'category': 'Customers',
                'title': c.name,
                'subtitle': f"Code: {c.customer_code} | City: {c.city or 'N/A'}",
                'url': "/sales/customers/"
            })

        # 4. Purchase Orders
        pos = PurchaseOrder.objects.filter(
            Q(po_number__icontains=query) | Q(supplier__name__icontains=query)
        )[:5]
        for po in pos:
            results.append({
                'category': 'Purchase Orders',
                'title': po.po_number,
                'subtitle': f"Supplier: {po.supplier.name} | Status: {po.status}",
                'url': f"/purchases/orders/{po.id}/"
            })

        # 5. Sales Invoices
        invoices = SalesInvoice.objects.filter(
            Q(invoice_number__icontains=query) | Q(customer__name__icontains=query)
        )[:5]
        for inv in invoices:
            results.append({
                'category': 'Sales Invoices',
                'title': inv.invoice_number,
                'subtitle': f"Customer: {inv.customer.name} | Total: ₹{inv.grand_total}",
                'url': "/sales/invoices/"
            })

        # 6. Warehouses
        warehouses = Warehouse.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(city__icontains=query)
        )[:5]
        for w in warehouses:
            results.append({
                'category': 'Warehouses',
                'title': w.name,
                'subtitle': f"Code: {w.code} | Location: {w.city or 'N/A'}",
                'url': "/products/warehouses/"
            })

        # 7. Batches
        batches = ProductBatch.objects.filter(batch_number__icontains=query)[:5]
        for b in batches:
            results.append({
                'category': 'Product Batches',
                'title': f"Batch #{b.batch_number}",
                'subtitle': f"Product: {b.product.name} | Exp: {b.expiry_date}",
                'url': "/batches/"
            })

        # 8. Employees
        employees = Employee.objects.filter(
            Q(full_name__icontains=query) | Q(employee_code__icontains=query)
        )[:5]
        for emp in employees:
            results.append({
                'category': 'Employees',
                'title': emp.full_name,
                'subtitle': f"Code: {emp.employee_code} | Dept: {emp.department.name if emp.department else 'N/A'}",
                'url': "/employees/"
            })

        return JsonResponse({'results': results})
