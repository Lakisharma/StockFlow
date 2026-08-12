from rest_framework import serializers
from .models import Brand

class BrandSerializer(serializers.ModelSerializer):
    total_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'code', 'description', 'logo', 'website',
            'status', 'total_products', 'created_at', 'updated_at'
        ]
        
    def get_total_products(self, obj):
        # Placeholder: will count related products when Product model is built in Step 8
        if hasattr(obj, 'product_set'):
            return obj.product_set.count()
        return 0
