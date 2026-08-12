import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from .models import Category
from .forms import CategoryForm

class CategoryListView(ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Category.objects.all()
        
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
        context['active_submenu'] = 'categories'
        context['q'] = self.request.GET.get('q', '')
        context['status'] = self.request.GET.get('status', 'all')
        context['sort'] = self.request.GET.get('sort', '-created_at')
        return context

    def get(self, request, *args, **kwargs):
        # Handle Export triggers before standard list view rendering
        export_format = request.GET.get('export')
        if export_format in ['csv', 'excel']:
            return self.export_categories(export_format)
        return super().get(request, *args, **kwargs)

    def export_categories(self, format):
        # Fetch current filtered/sorted queryset (ignoring pagination)
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f"categories_export.{format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        # Headers matching table columns
        writer.writerow(['Category Name', 'Category Code', 'Description', 'Total Products', 'Status', 'Created Date', 'Updated Date'])
        
        for cat in queryset:
            # count products (placeholder 0 for now)
            total_products = cat.product_set.count() if hasattr(cat, 'product_set') else 0
            writer.writerow([
                cat.name,
                cat.code,
                cat.description,
                total_products,
                cat.status.capitalize(),
                cat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                cat.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'categories/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'categories'
        return context

class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category-list')
    success_message = "Category '%(name)s' was created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'categories'
        context['title'] = "Add New Category"
        return context

class CategoryUpdateView(SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category-list')
    success_message = "Category '%(name)s' was updated successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_menu'] = 'inventory'
        context['active_submenu'] = 'categories'
        context['title'] = f"Edit Category: {self.object.name}"
        return context

class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('category-list')
    
    def post(self, request, *args, **kwargs):
        category = self.get_object()
        # Prevent deletion if related products exist (placeholder check)
        if hasattr(category, 'product_set') and category.product_set.exists():
            messages.error(request, f"Cannot delete category '{category.name}' because it contains products.")
            return redirect('category-list')
            
        messages.success(request, f"Category '{category.name}' was deleted successfully.")
        return super().post(request, *args, **kwargs)

# Bulk actions view
def category_bulk_delete(request):
    if request.method == 'POST':
        category_ids = request.POST.getlist('ids')
        if category_ids:
            # Fetch categories to delete
            categories = Category.objects.filter(id__in=category_ids)
            count = 0
            skipped = 0
            for cat in categories:
                # Safe check: if products exist, skip
                if hasattr(cat, 'product_set') and cat.product_set.exists():
                    skipped += 1
                else:
                    cat.delete()
                    count += 1
            
            if count > 0:
                messages.success(request, f"Successfully deleted {count} categories.")
            if skipped > 0:
                messages.warning(request, f"Skipped {skipped} categories because they contain products.")
        else:
            messages.warning(request, "No categories selected for bulk deletion.")
    return redirect('category-list')
