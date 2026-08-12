from .models import (
    CompanyProfile, BusinessInfo, TaxSettings, InvoiceSettings,
    CurrencySettings, WarehouseConfig, InventoryConfig, PurchaseConfig,
    OCRAISettings, NotificationSettings, SecuritySettings, SystemPreferences
)

class SystemSettingsService:

    @classmethod
    def get_company_profile(cls):
        obj, _ = CompanyProfile.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_business_info(cls):
        obj, _ = BusinessInfo.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_tax_settings(cls):
        obj, _ = TaxSettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_invoice_settings(cls):
        obj, _ = InvoiceSettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_currency_settings(cls):
        obj, _ = CurrencySettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_warehouse_config(cls):
        obj, _ = WarehouseConfig.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_inventory_config(cls):
        obj, _ = InventoryConfig.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_purchase_config(cls):
        obj, _ = PurchaseConfig.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_ocr_settings(cls):
        obj, _ = OCRAISettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_notification_settings(cls):
        obj, _ = NotificationSettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_security_settings(cls):
        obj, _ = SecuritySettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_system_preferences(cls):
        obj, _ = SystemPreferences.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_all_settings(cls):
        return {
            'company': cls.get_company_profile(),
            'business': cls.get_business_info(),
            'tax': cls.get_tax_settings(),
            'invoice': cls.get_invoice_settings(),
            'currency': cls.get_currency_settings(),
            'warehouse': cls.get_warehouse_config(),
            'inventory': cls.get_inventory_config(),
            'purchase': cls.get_purchase_config(),
            'ocr': cls.get_ocr_settings(),
            'notification': cls.get_notification_settings(),
            'security': cls.get_security_settings(),
            'preferences': cls.get_system_preferences(),
        }
