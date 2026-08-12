import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from .models import Unit
from .forms import UnitForm

class UnitListView(ListView):
    model = Unit
    template_name = 'units/unit_list.html'
    context_object_name = 'units'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Unit.objects.all()
        
        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(short_name__icontains=query)
            )
            
        # Status filter
        status = self.request.GET.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['name', '-name', 'short_name', '-short_name', 'created_at', '-created_at']
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'units'
        context['q'] = self.request.GET.get('q', '')
        context['status'] = self.request.GET.get('status', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export triggers before list view rendering
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_units(export_format)
        return super().get(request, *args, **kwargs)

    def export_units(self, format):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"units_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Unit Name', 'Short Name', 'Description', 'Total Products', 'Status', 'Created Date', 'Updated Date'])
        
        for unit in queryset:
            total_products = unit.product_set.count() if hasattr(unit, 'product_set') else 0
            writer.writerow([
                unit.name,
                unit.short_name,
                unit.description,
                total_products,
                unit.status.capitalize(),
                unit.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                unit.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class UnitDetailView(DetailView):
    model = Unit
    template_name = 'units/unit_detail.html'
    context_object_name = 'unit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'units'
        return context

class UnitCreateView(SuccessMessageMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'units/unit_form.html'
    success_url = reverse_lazy('unit-list')
    success_message = "Unit '%(name)s' was created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'units'
        context['title'] = "Add New Unit"
        return context

class UnitUpdateView(SuccessMessageMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'units/unit_form.html'
    success_url = reverse_lazy('unit-list')
    success_message = "Unit '%(name)s' was updated successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'units'
        context['title'] = f"Edit Unit: {self.object.name}"
        return context

class UnitDeleteView(DeleteView):
    model = Unit
    template_name = 'units/unit_confirm_delete.html'
    success_url = reverse_lazy('unit-list')
    
    def post(self, request, *args, **kwargs):
        unit = self.get_object()
        # Prevent deletion if related products exist (placeholder check)
        if hasattr(unit, 'product_set') and unit.product_set.exists():
            messages.error(request, f"Cannot delete unit '{unit.name}' because it contains products.")
            return redirect('unit-list')
            
        messages.success(request, f"Unit '{unit.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def unit_bulk_delete(request):
    if request.method == 'POST':
        unit_ids = request.POST.getlist('ids')
        if unit_ids:
            units = Unit.objects.filter(id__in=unit_ids)
            count = 0
            skipped = 0
            for unit in units:
                if hasattr(unit, 'product_set') and unit.product_set.exists():
                    skipped += 1
                else:
                    unit.delete()
                    count += 1
            
            if count > 0:
                messages.success(request, f"Successfully deleted {count} units.")
            if skipped > 0:
                messages.warning(request, f"Skipped {skipped} units because they contain products.")
        else:
            messages.warning(request, "No units selected for bulk deletion.")
    return redirect('unit-list')
