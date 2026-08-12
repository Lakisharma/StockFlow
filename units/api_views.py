from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Unit
from .serializers import UnitSerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'short_name']
    ordering_fields = ['created_at', 'name', 'short_name']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
        return queryset
