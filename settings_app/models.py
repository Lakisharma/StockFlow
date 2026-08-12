from django.db import models
from datetime import date

class CompanyProfile(models.Model):
    company_name = models.CharField(max_length=150, default='StockFlow Enterprise Pvt Ltd')
    legal_name = models.CharField(max_length=150, default='StockFlow Enterprise Private Limited')
    business_type = models.CharField(max_length=100, default='Private Limited Company')
    email = models.EmailField(default='contact@stockflow.ai')
    phone = models.CharField(max_length=20, default='+91 9876543210')
    alt_phone = models.CharField(max_length=20, blank=True, null=True, default='+91 1123456789')
    website = models.URLField(default='https://stockflow.ai')
    address = models.TextField(default='Plot 42, Tech Park Sector 62')
    city = models.CharField(max_length=100, default='Noida')
    state = models.CharField(max_length=100, default='Uttar Pradesh')
    country = models.CharField(max_length=100, default='India')
    pin_code = models.CharField(max_length=10, default='201301')
    company_logo = models.ImageField(upload_to='company/logos/', blank=True, null=True)

    def __str__(self):
        return self.company_name

class BusinessInfo(models.Model):
    registration_number = models.CharField(max_length=50, default='REG-2026-IN889')
    gstin = models.CharField(max_length=20, default='09AAACS1234F1Z5')
    pan = models.CharField(max_length=20, default='AAACS1234F')
    cin = models.CharField(max_length=30, blank=True, null=True, default='U72900UP2026PTC123456')
    tax_type = models.CharField(max_length=50, default='Regular Scheme')
    industry = models.CharField(max_length=100, default='Electronics & FMCG Distribution')
    description = models.TextField(default='Enterprise Multi-Warehouse Inventory & Supply Chain Management System')
    fy_start_date = models.DateField(default=date(2026, 4, 1))
    fy_end_date = models.DateField(default=date(2027, 3, 31))

    def __str__(self):
        return f"Business Info ({self.gstin})"

class TaxSettings(models.Model):
    gst_enabled = models.BooleanField(default=True)
    default_gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    utgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    hsn_required = models.BooleanField(default=True)
    price_tax_type = models.CharField(max_length=20, choices=[('exclusive', 'Tax Exclusive'), ('inclusive', 'Tax Inclusive')], default='exclusive')

class InvoiceSettings(models.Model):
    sales_prefix = models.CharField(max_length=10, default='INV-')
    purchase_prefix = models.CharField(max_length=10, default='PUR-')
    po_prefix = models.CharField(max_length=10, default='PO-')
    transfer_prefix = models.CharField(max_length=10, default='TRF-')
    starting_invoice_number = models.IntegerField(default=1001)
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    footer_text = models.TextField(default='Thank you for choosing StockFlow AI Enterprise Solutions.')
    terms_conditions = models.TextField(default='1. Goods once sold cannot be returned without authorization.\n2. Interest @ 18% p.a. charged on overdue invoices.')
    show_gstin = models.BooleanField(default=True)
    show_hsn = models.BooleanField(default=True)
    show_discount = models.BooleanField(default=True)
    show_payment_details = models.BooleanField(default=True)
    authorized_signature = models.ImageField(upload_to='company/signatures/', blank=True, null=True)

class CurrencySettings(models.Model):
    currency_code = models.CharField(max_length=10, default='INR')
    currency_symbol = models.CharField(max_length=5, default='₹')
    country = models.CharField(max_length=50, default='India')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    number_format = models.CharField(max_length=20, default='1,50,000.00')
    decimal_places = models.IntegerField(default=2)

class WarehouseConfig(models.Model):
    allow_multiple_warehouses = models.BooleanField(default=True)
    code_format = models.CharField(max_length=20, default='WH-{001}')
    allow_warehouse_transfer = models.BooleanField(default=True)
    require_transfer_approval = models.BooleanField(default=True)
    allow_negative_stock = models.BooleanField(default=False)

class InventoryConfig(models.Model):
    VALUATION_CHOICES = [
        ('FIFO', 'First In First Out (FIFO)'),
        ('WEIGHTED_AVG', 'Weighted Average'),
        ('MOVING_AVG', 'Moving Average'),
    ]
    valuation_method = models.CharField(max_length=20, choices=VALUATION_CHOICES, default='FIFO')
    low_stock_threshold_default = models.IntegerField(default=10)
    batch_tracking = models.BooleanField(default=True)
    expiry_tracking = models.BooleanField(default=True)
    serial_number_tracking = models.BooleanField(default=False)
    barcode_tracking = models.BooleanField(default=True)
    qr_code_tracking = models.BooleanField(default=True)

class PurchaseConfig(models.Model):
    purchase_order_required = models.BooleanField(default=True)
    purchase_approval_required = models.BooleanField(default=True)
    goods_receipt_required = models.BooleanField(default=True)
    allow_partial_receiving = models.BooleanField(default=True)
    allow_purchase_return = models.BooleanField(default=True)
    duplicate_invoice_detection = models.BooleanField(default=True)
    default_payment_terms = models.CharField(max_length=50, default='Net 30 Days')

class OCRAISettings(models.Model):
    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini AI Engine'),
        ('tesseract', 'Tesseract OCR Engine'),
        ('google_vision', 'Google Cloud Vision API'),
        ('azure', 'Azure Document Intelligence'),
        ('aws', 'AWS Textract'),
    ]
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='gemini')
    api_key_masked = models.CharField(max_length=200, default='AIzaSy********************')
    model_name = models.CharField(max_length=50, default='gemini-1.5-pro')
    confidence_threshold = models.IntegerField(default=75)
    max_file_size_mb = models.IntegerField(default=20)
    allowed_file_types = models.CharField(max_length=100, default='PDF, JPG, JPEG, PNG, WEBP')

class NotificationSettings(models.Model):
    notify_low_stock = models.BooleanField(default=True)
    notify_out_of_stock = models.BooleanField(default=True)
    notify_purchase_created = models.BooleanField(default=True)
    notify_purchase_approved = models.BooleanField(default=True)
    notify_stock_transfer = models.BooleanField(default=True)
    notify_ocr_completed = models.BooleanField(default=True)
    notify_user_login = models.BooleanField(default=True)
    channel_email = models.BooleanField(default=True)
    channel_in_app = models.BooleanField(default=True)

class SecuritySettings(models.Model):
    session_timeout_minutes = models.IntegerField(default=30)
    password_min_length = models.IntegerField(default=8)
    password_expiry_days = models.IntegerField(default=90)
    max_login_attempts = models.IntegerField(default=5)
    account_lockout_minutes = models.IntegerField(default=15)
    require_strong_password = models.BooleanField(default=True)
    enable_two_factor = models.BooleanField(default=False)

class SystemPreferences(models.Model):
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('auto', 'System Default'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    items_per_page = models.IntegerField(default=25)
    default_report_period = models.CharField(max_length=20, default='this_month')
    compact_table_mode = models.BooleanField(default=False)
    enable_animations = models.BooleanField(default=True)
