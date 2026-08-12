from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category
from .serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['created_at', 'name', 'code']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
        return queryset
