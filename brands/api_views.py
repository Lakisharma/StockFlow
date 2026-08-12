from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Brand
from .serializers import BrandSerializer

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
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
