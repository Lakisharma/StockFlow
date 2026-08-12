from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from products.models import Product, Warehouse, WarehouseStock
from batches.models import ProductBatch, ProductSerialNumber
from .models import Customer, SalesOrder, SalesOrderItem, PickList, PickListItem, Dispatch, DispatchItem, SalesInvoice
from .services import SalesService

class CustomerListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        qs = Customer.objects.all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(customer_code__icontains=search) | Q(phone__icontains=search) | Q(gstin__icontains=search))

        total_customers = Customer.objects.count()
        total_outstanding = Customer.objects.aggregate(total=Sum('outstanding_amount'))['total'] or 0

        context = {
            'customers': qs[:100],
            'total_customers': total_customers,
            'total_outstanding': total_outstanding,
            'auto_customer_code': SalesService.generate_customer_code(),
            'search': search,
            'active_menu': 'sales'
        }
        return render(request, 'sales/customer_list.html', context)

    def post(self, request):
        name = request.POST.get('name')
        business_name = request.POST.get('business_name', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        gstin = request.POST.get('gstin', '')
        billing_address = request.POST.get('billing_address', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        pincode = request.POST.get('pincode', '')
        credit_limit = float(request.POST.get('credit_limit', 0))

        cust = Customer.objects.create(
            customer_code=SalesService.generate_customer_code(),
            name=name,
            business_name=business_name,
            phone=phone,
            email=email,
            gstin=gstin,
            billing_address=billing_address,
            shipping_address=billing_address,
            city=city,
            state=state,
            pincode=pincode,
            credit_limit=credit_limit,
            status='active'
        )

        messages.success(request, f"Customer '{cust.name}' ({cust.customer_code}) created successfully.")
        return redirect('customer-list')

class SalesOrderListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = SalesOrder.objects.select_related('customer', 'warehouse', 'created_by').all()
        search = request.GET.get('search')
        status_filter = request.GET.get('status')

        if search:
            qs = qs.filter(Q(so_number__icontains=search) | Q(customer__name__icontains=search) | Q(warehouse__name__icontains=search))
        if status_filter:
            qs = qs.filter(status=status_filter)

        total_orders = SalesOrder.objects.count()
        pending_approval = SalesOrder.objects.filter(status='pending_approval').count()
        ready_for_dispatch = SalesOrder.objects.filter(status__in=['approved', 'ready_for_dispatch']).count()
        dispatched_count = SalesOrder.objects.filter(status='dispatched').count()

        context = {
            'orders': qs[:100],
            'total_orders': total_orders,
            'pending_approval': pending_approval,
            'ready_for_dispatch': ready_for_dispatch,
            'dispatched_count': dispatched_count,
            'search': search,
            'status_filter': status_filter,
            'active_menu': 'sales'
        }
        return render(request, 'sales/so_list.html', context)

class SalesOrderCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        customers = Customer.objects.filter(status='active')
        warehouses = Warehouse.objects.filter(status='active')
        products = Product.objects.filter(status='active')

        context = {
            'auto_so_number': SalesService.generate_so_number(),
            'customers': customers,
            'warehouses': warehouses,
            'products': products,
            'active_menu': 'sales'
        }
        return render(request, 'sales/so_create.html', context)

    def post(self, request):
        so_number = request.POST.get('so_number') or SalesService.generate_so_number()
        customer_id = request.POST.get('customer')
        warehouse_id = request.POST.get('warehouse')
        order_date = request.POST.get('order_date') or timezone.now().date()
        expected_dispatch_date = request.POST.get('expected_dispatch_date') or None
        payment_terms = request.POST.get('payment_terms', 'Net 30')
        notes = request.POST.get('notes', '')

        cust = get_object_or_404(Customer, pk=customer_id)
        wh = get_object_or_404(Warehouse, pk=warehouse_id)

        so = SalesOrder.objects.create(
            so_number=so_number,
            customer=cust,
            warehouse=wh,
            order_date=order_date,
            expected_dispatch_date=expected_dispatch_date,
            payment_terms=payment_terms,
            billing_address=cust.billing_address,
            shipping_address=cust.shipping_address or cust.billing_address,
            notes=notes,
            status='draft',
            created_by=request.user
        )

        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        rates = request.POST.getlist('rate[]')
        gsts = request.POST.getlist('gst[]')

        subtotal = 0
        total_tax = 0

        for i in range(len(product_ids)):
            try:
                prod = Product.objects.get(pk=product_ids[i])
                qty = int(quantities[i])
                rate = float(rates[i])
                gst_pct = float(gsts[i]) if gsts[i] else (prod.gst_rate or 0.0)
            except (ValueError, Product.DoesNotExist, IndexError):
                continue

            line_sub = qty * rate
            line_tax = line_sub * (gst_pct / 100.0)
            line_tot = line_sub + line_tax

            subtotal += line_sub
            total_tax += line_tax

            SalesOrderItem.objects.create(
                sales_order=so,
                product=prod,
                ordered_quantity=qty,
                rate=rate,
                gst_percent=gst_pct,
                line_total=line_tot
            )

        so.subtotal = subtotal
        so.tax_amount = total_tax
        so.grand_total = subtotal + total_tax
        so.save()

        action_type = request.POST.get('action_type')
        if action_type == 'submit':
            SalesService.submit_so_for_approval(so, request.user)
            messages.success(request, f"Sales Order '{so.so_number}' created and submitted for approval.")
        else:
            messages.success(request, f"Draft Sales Order '{so.so_number}' saved successfully.")

        return redirect('so-detail', pk=so.id)

class SalesOrderDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        so = get_object_or_404(SalesOrder.objects.select_related('customer', 'warehouse', 'created_by').prefetch_related('items__product', 'pick_lists', 'dispatches'), pk=pk)

        # Check warehouse stock availability
        item_stock_warnings = []
        for item in so.items.all():
            stock_rec = WarehouseStock.objects.filter(product=item.product, warehouse=so.warehouse).first()
            avail = stock_rec.quantity if stock_rec else 0
            if avail < item.ordered_quantity:
                item_stock_warnings.append(f"Product '{item.product.name}': Ordered {item.ordered_quantity}, but only {avail} available in {so.warehouse.name}.")

        context = {
            'so': so,
            'item_stock_warnings': item_stock_warnings,
            'active_menu': 'sales'
        }
        return render(request, 'sales/so_detail.html', context)

    def post(self, request, pk):
        so = get_object_or_404(SalesOrder, pk=pk)
        action = request.POST.get('action')

        if action == 'submit':
            SalesService.submit_so_for_approval(so, request.user)
            messages.success(request, f"Sales Order '{so.so_number}' submitted for approval.")
        elif action == 'approve':
            SalesService.approve_so(so, request.user)
            messages.success(request, f"Sales Order '{so.so_number}' approved successfully.")

        return redirect('so-detail', pk=so.id)

class SalesOrderPrintView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        so = get_object_or_404(SalesOrder.objects.select_related('customer', 'warehouse', 'created_by').prefetch_related('items__product'), pk=pk)
        return render(request, 'sales/so_print.html', {'so': so})

class PickingCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        so_id = request.GET.get('so')
        if not so_id:
            messages.warning(request, "Please select an approved Sales Order to begin picking.")
            return redirect('so-list')

        so = get_object_or_404(SalesOrder.objects.select_related('customer', 'warehouse').prefetch_related('items__product'), pk=so_id)

        # Fetch FEFO recommended batches for items in order
        picking_items = []
        if so:
            for item in so.items.all():
                batches = ProductBatch.objects.filter(product=item.product, warehouse=so.warehouse, available_quantity__gt=0, status__in=['active', 'expiring_soon']).order_by('expiry_date')
                serials = ProductSerialNumber.objects.filter(product=item.product, warehouse=so.warehouse, status='in_stock')
                picking_items.append({
                    'item': item,
                    'recommended_batch': batches.first(),
                    'batches': batches,
                    'serials': serials
                })

        context = {
            'auto_pick_number': SalesService.generate_pick_number(),
            'so': so,
            'picking_items': picking_items,
            'active_menu': 'sales'
        }
        return render(request, 'sales/picking_create.html', context)

    def post(self, request):
        so_id = request.POST.get('sales_order')
        so = get_object_or_404(SalesOrder, pk=so_id)

        pick = PickList.objects.create(
            pick_list_number=SalesService.generate_pick_number(),
            sales_order=so,
            warehouse=so.warehouse,
            assigned_to=request.user,
            status='completed'
        )

        so_item_ids = request.POST.getlist('so_item_id[]')
        product_ids = request.POST.getlist('product_id[]')
        picked_qtys = request.POST.getlist('picked_qty[]')
        batch_numbers = request.POST.getlist('batch_number[]')
        serial_raws = request.POST.getlist('serials[]')

        for i in range(len(product_ids)):
            try:
                so_item = SalesOrderItem.objects.get(pk=so_item_ids[i])
                prod = Product.objects.get(pk=product_ids[i])
                p_qty = int(picked_qtys[i])
                b_num = batch_numbers[i] if i < len(batch_numbers) else ''
                s_list = [s.strip() for s in serial_raws[i].split(',') if s.strip()] if i < len(serial_raws) else []
            except (ValueError, SalesOrderItem.DoesNotExist, Product.DoesNotExist, IndexError):
                continue

            PickListItem.objects.create(
                pick_list=pick,
                so_item=so_item,
                product=prod,
                ordered_quantity=so_item.ordered_quantity,
                picked_quantity=p_qty,
                batch_number=b_num,
                serial_numbers=s_list
            )

            so_item.picked_quantity = p_qty
            so_item.save()

        so.status = 'ready_for_dispatch'
        so.save()

        messages.success(request, f"Pick List '{pick.pick_list_number}' completed. Order '{so.so_number}' is ready for dispatch.")
        return redirect('so-detail', pk=so.id)

class DispatchListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = Dispatch.objects.select_related('sales_order', 'customer', 'warehouse', 'created_by').all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(dispatch_number__icontains=search) | Q(customer__name__icontains=search) | Q(tracking_number__icontains=search))

        context = {
            'dispatches': qs[:100],
            'search': search,
            'active_menu': 'sales'
        }
        return render(request, 'sales/dispatch_list.html', context)

class DispatchConfirmView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        dispatch = get_object_or_404(Dispatch, pk=pk)
        SalesService.confirm_dispatch(dispatch, request.user)
        messages.success(request, f"Dispatch '{dispatch.dispatch_number}' confirmed. Inventory stock out completed successfully.")
        return redirect('dispatch-list')

class SalesInvoiceListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = SalesInvoice.objects.select_related('customer', 'warehouse', 'sales_order').all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(invoice_number__icontains=search) | Q(customer__name__icontains=search))

        context = {
            'invoices': qs[:100],
            'search': search,
            'active_menu': 'sales'
        }
        return render(request, 'sales/invoice_list.html', context)

class SalesInvoiceDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        invoice = get_object_or_404(SalesInvoice.objects.select_related('customer', 'warehouse', 'sales_order', 'dispatch'), pk=pk)
        return render(request, 'sales/invoice_detail.html', {'invoice': invoice, 'active_menu': 'sales'})

class SalesInvoicePrintView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        invoice = get_object_or_404(SalesInvoice.objects.select_related('customer', 'warehouse', 'sales_order'), pk=pk)
        return render(request, 'sales/invoice_print.html', {'invoice': invoice})
