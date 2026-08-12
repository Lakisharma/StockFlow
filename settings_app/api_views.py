from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import SystemSettingsService
from .serializers import CompanyProfileSerializer, TaxSettingsSerializer, CurrencySettingsSerializer

class SystemSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        comp = SystemSettingsService.get_company_profile()
        tax = SystemSettingsService.get_tax_settings()
        curr = SystemSettingsService.get_currency_settings()

        return Response({
            'company': CompanyProfileSerializer(comp).data,
            'tax': TaxSettingsSerializer(tax).data,
            'currency': CurrencySettingsSerializer(curr).data,
        }, status=status.HTTP_200_OK)
