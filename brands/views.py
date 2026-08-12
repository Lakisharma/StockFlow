import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from .models import Brand
from .forms import BrandForm

class BrandListView(ListView):
    model = Brand
    template_name = 'brands/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Brand.objects.all()
        
        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
            
        # Status filter
        status = self.request.GET.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = ['name', '-name', 'code', '-code', 'created_at', '-created_at']
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'brands'
        context['q'] = self.request.GET.get('q', '')
        context['status'] = self.request.GET.get('status', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export triggers before list view rendering
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_brands(export_format)
        return super().get(request, *args, **kwargs)

    def export_brands(self, format):
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"brands_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Brand Name', 'Brand Code', 'Description', 'Website', 'Total Products', 'Status', 'Created Date', 'Updated Date'])
        
        for brand in queryset:
            total_products = brand.product_set.count() if hasattr(brand, 'product_set') else 0
            writer.writerow([
                brand.name,
                brand.code,
                brand.description,
                brand.website,
                total_products,
                brand.status.capitalize(),
                brand.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                brand.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class BrandDetailView(DetailView):
    model = Brand
    template_name = 'brands/brand_detail.html'
    context_object_name = 'brand'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'brands'
        return context

class BrandCreateView(SuccessMessageMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'brands/brand_form.html'
    success_url = reverse_lazy('brand-list')
    success_message = "Brand '%(name)s' was created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'brands'
        context['title'] = "Add New Brand"
        return context

class BrandUpdateView(SuccessMessageMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'brands/brand_form.html'
    success_url = reverse_lazy('brand-list')
    success_message = "Brand '%(name)s' was updated successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'brands'
        context['title'] = f"Edit Brand: {self.object.name}"
        return context

class BrandDeleteView(DeleteView):
    model = Brand
    template_name = 'brands/brand_confirm_delete.html'
    success_url = reverse_lazy('brand-list')
    
    def post(self, request, *args, **kwargs):
        brand = self.get_object()
        # Prevent deletion if related products exist (placeholder check)
        if hasattr(brand, 'product_set') and brand.product_set.exists():
            messages.error(request, f"Cannot delete brand '{brand.name}' because it contains products.")
            return redirect('brand-list')
            
        messages.success(request, f"Brand '{brand.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def brand_bulk_delete(request):
    if request.method == 'POST':
        brand_ids = request.POST.getlist('ids')
        if brand_ids:
            brands = Brand.objects.filter(id__in=brand_ids)
            count = 0
            skipped = 0
            for brand in brands:
                if hasattr(brand, 'product_set') and brand.product_set.exists():
                    skipped += 1
                else:
                    brand.delete()
                    count += 1
            
            if count > 0:
                messages.success(request, f"Successfully deleted {count} brands.")
            if skipped > 0:
                messages.warning(request, f"Skipped {skipped} brands because they contain products.")
        else:
            messages.warning(request, "No brands selected for bulk deletion.")
    return redirect('brand-list')
