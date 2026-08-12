import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from .models import Supplier, SupplierHistory
from .forms import SupplierForm

class SupplierListView(ListView):
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Supplier.objects.all()
        
        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(company_name__icontains=query) |
                Q(contact_person__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query) |
                Q(gstin__icontains=query)
            )
            
        # Status Filter
        status = self.request.GET.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        # Payment Status Filter
        pay_status = self.request.GET.get('payment_status')
        if pay_status == 'overdue':
            queryset = queryset.filter(outstanding_balance__gt=0)
        elif pay_status == 'pending':
            queryset = queryset.filter(outstanding_balance__gt=0)
        elif pay_status == 'paid':
            queryset = queryset.filter(outstanding_balance__lte=0)
            
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['name', '-name', 'code', '-code', 'company_name', '-company_name', 'outstanding_balance', '-outstanding_balance', 'created_at', '-created_at']
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'suppliers'
        context['active_submenu'] = 'suppliers'
        
        # Current filter states
        context['q'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', 'all')
        context['selected_payment_status'] = self.request.GET.get('payment_status', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export triggers
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_suppliers(export_format)
        return super().get(request, *args, **kwargs)

    def export_suppliers(self, format):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"suppliers_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Supplier Name', 'Supplier Code', 'Company Name', 'Contact Person', 'Type', 'Status',
            'Phone', 'Email', 'Website', 'Address', 'City', 'State', 'Country', 'PIN Code',
            'GSTIN', 'PAN', 'Outstanding Balance', 'Credit Limit'
        ])
        
        for sup in queryset:
            writer.writerow([
                sup.name,
                sup.code,
                sup.company_name,
                sup.contact_person,
                sup.supplier_type.capitalize(),
                sup.status.capitalize(),
                sup.phone,
                sup.email,
                sup.website,
                sup.address,
                sup.city,
                sup.state,
                sup.country,
                sup.pin_code,
                sup.gstin,
                sup.pan,
                sup.outstanding_balance,
                sup.credit_limit
            ])
            
        return response

class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'
    context_object_name = 'supplier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'suppliers'
        context['active_submenu'] = 'suppliers'
        
        # Simulated Purchase Statistics / Summaries (will connect to actual purchase models later)
        # We can calculate values based on the supplier's outstanding balance
        outstanding = self.object.outstanding_balance
        context['purchase_stats'] = {
            'total_orders': 15 if outstanding > 0 else 5,
            'total_bills': 12 if outstanding > 0 else 5,
            'total_amount': float(outstanding) * 4.5 + 500.0,
            'paid_amount': float(outstanding) * 3.5,
            'pending_amount': float(outstanding),
            'overdue_amount': float(outstanding) * 0.3 if outstanding > 0 else 0.0,
        }
        
        # Simulated Purchase History Logs
        context['purchase_history'] = [
            {
                'invoice_number': f"INV-2026-{1000 + i}",
                'purchase_date': f"2026-08-0{i}",
                'amount': float(outstanding) * 1.5 if i == 1 else 150.0,
                'paid_amount': float(outstanding) * 0.8 if i == 1 else 150.0,
                'pending_amount': float(outstanding) * 0.7 if i == 1 else 0.0,
                'status': 'Pending' if i == 1 and outstanding > 0 else 'Paid',
            } for i in range(1, 4)
        ]
        
        # Timeline action history logs
        context['history_logs'] = self.object.histories.all()[:15]
        return context

class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier '%(name)s' was created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'suppliers'
        context['active_submenu'] = 'suppliers'
        context['title'] = "Add New Supplier"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        SupplierHistory.objects.create(
            supplier=self.object,
            action="created",
            detail=f"Supplier '{self.object.name}' was created with opening outstanding balance of {self.object.outstanding_balance}."
        )
        return response

class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    success_message = "Supplier '%(name)s' was updated successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'suppliers'
        context['active_submenu'] = 'suppliers'
        context['title'] = f"Edit Supplier: {self.object.name}"
        return context

    def form_valid(self, form):
        old_supplier = Supplier.objects.get(pk=self.kwargs['pk'])
        old_outstanding = old_supplier.outstanding_balance
        
        response = super().form_valid(form)
        
        details = []
        if old_outstanding != self.object.outstanding_balance:
            details.append(f"Outstanding balance changed from {old_outstanding} to {self.object.outstanding_balance}")
            SupplierHistory.objects.create(
                supplier=self.object,
                action="payment_updated",
                detail=f"Outstanding balance adjusted from {old_outstanding} to {self.object.outstanding_balance}."
            )
            
        SupplierHistory.objects.create(
            supplier=self.object,
            action="updated",
            detail=f"Supplier information modified. {', '.join(details) if details else ''}"
        )
        return response

class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'suppliers/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if supplier has simulated transactions or outstanding balances
        # In a real system we would filter PurchaseOrder.objects.filter(supplier=self.object)
        # For now, we check if outstanding_balance > 0
        context['has_records'] = self.object.outstanding_balance > 0 or self.object.opening_balance > 0
        return context
        
    def post(self, request, *args, **kwargs):
        supplier = self.get_object()
        has_records = supplier.outstanding_balance > 0 or supplier.opening_balance > 0
        deactivate_only = request.POST.get('deactivate_only') == 'true'
        
        if has_records or deactivate_only:
            # Enforce deactivation instead of hard delete
            supplier.status = 'inactive'
            supplier.save()
            SupplierHistory.objects.create(
                supplier=supplier,
                action="deactivated",
                detail="Supplier deactivated due to associated transactions or active balance settings."
            )
            messages.success(request, f"Supplier '{supplier.name}' has active balances and was deactivated successfully.")
            return redirect('supplier-list')
            
        messages.success(request, f"Supplier '{supplier.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def supplier_bulk_action(request):
    if request.method == 'POST':
        supplier_ids = request.POST.getlist('ids')
        action = request.POST.get('action')
        
        if supplier_ids:
            suppliers = Supplier.objects.filter(id__in=supplier_ids)
            if action == 'delete':
                # Filter out suppliers with active balances for safety
                safe_delete_qs = suppliers.filter(outstanding_balance__lte=0, opening_balance__lte=0)
                unsafe_delete_qs = suppliers.filter(Q(outstanding_balance__gt=0) | Q(opening_balance__gt=0))
                
                count_del = safe_delete_qs.delete()[0] if safe_delete_qs.exists() else 0
                count_deact = unsafe_delete_qs.update(status='inactive') if unsafe_delete_qs.exists() else 0
                
                msg = []
                if count_del > 0:
                    msg.append(f"deleted {count_del} suppliers")
                if count_deact > 0:
                    msg.append(f"deactivated {count_deact} suppliers (due to transaction logs)")
                    
                messages.success(request, f"Successfully {', and '.join(msg)}.")
            elif action == 'deactivate':
                count = suppliers.update(status='inactive')
                messages.success(request, f"Successfully deactivated {count} suppliers.")
            elif action == 'activate':
                count = suppliers.update(status='active')
                messages.success(request, f"Successfully activated {count} suppliers.")
        else:
            messages.warning(request, "No suppliers selected.")
            
    return redirect('supplier-list')
