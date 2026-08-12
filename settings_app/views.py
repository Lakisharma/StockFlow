from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from users.services import RBACService
from .services import SystemSettingsService

class SettingsMainView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Check permissions: Super Admin or user with settings view permission
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'view'):
            messages.error(request, "You do not have administrative authorization to access System Settings.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        section = request.GET.get('section', 'company')
        all_settings = SystemSettingsService.get_all_settings()
        all_settings['active_section'] = section
        return render(request, 'settings_app/settings_index.html', all_settings)

    def post(self, request):
        section = request.POST.get('section', 'company')
        all_settings = SystemSettingsService.get_all_settings()

        if section == 'company':
            comp = all_settings['company']
            comp.company_name = request.POST.get('company_name', comp.company_name)
            comp.legal_name = request.POST.get('legal_name', comp.legal_name)
            comp.business_type = request.POST.get('business_type', comp.business_type)
            comp.email = request.POST.get('email', comp.email)
            comp.phone = request.POST.get('phone', comp.phone)
            comp.alt_phone = request.POST.get('alt_phone', comp.alt_phone)
            comp.website = request.POST.get('website', comp.website)
            comp.address = request.POST.get('address', comp.address)
            comp.city = request.POST.get('city', comp.city)
            comp.state = request.POST.get('state', comp.state)
            comp.country = request.POST.get('country', comp.country)
            comp.pin_code = request.POST.get('pin_code', comp.pin_code)
            if 'company_logo' in request.FILES:
                comp.company_logo = request.FILES['company_logo']
            comp.save()
            messages.success(request, "Company Profile updated successfully.")

        elif section == 'business':
            biz = all_settings['business']
            biz.registration_number = request.POST.get('registration_number', biz.registration_number)
            biz.gstin = request.POST.get('gstin', biz.gstin)
            biz.pan = request.POST.get('pan', biz.pan)
            biz.cin = request.POST.get('cin', biz.cin)
            biz.tax_type = request.POST.get('tax_type', biz.tax_type)
            biz.industry = request.POST.get('industry', biz.industry)
            biz.description = request.POST.get('description', biz.description)
            biz.save()
            messages.success(request, "Business Information updated successfully.")

        elif section == 'tax':
            tax = all_settings['tax']
            tax.gst_enabled = request.POST.get('gst_enabled') == 'on'
            tax.default_gst_rate = request.POST.get('default_gst_rate', tax.default_gst_rate)
            tax.cgst_rate = request.POST.get('cgst_rate', tax.cgst_rate)
            tax.sgst_rate = request.POST.get('sgst_rate', tax.sgst_rate)
            tax.igst_rate = request.POST.get('igst_rate', tax.igst_rate)
            tax.hsn_required = request.POST.get('hsn_required') == 'on'
            tax.price_tax_type = request.POST.get('price_tax_type', tax.price_tax_type)
            tax.save()
            messages.success(request, "Tax & GST Settings updated successfully.")

        elif section == 'invoice':
            inv = all_settings['invoice']
            inv.sales_prefix = request.POST.get('sales_prefix', inv.sales_prefix)
            inv.purchase_prefix = request.POST.get('purchase_prefix', inv.purchase_prefix)
            inv.po_prefix = request.POST.get('po_prefix', inv.po_prefix)
            inv.transfer_prefix = request.POST.get('transfer_prefix', inv.transfer_prefix)
            inv.starting_invoice_number = request.POST.get('starting_invoice_number', inv.starting_invoice_number)
            inv.footer_text = request.POST.get('footer_text', inv.footer_text)
            inv.terms_conditions = request.POST.get('terms_conditions', inv.terms_conditions)
            inv.show_gstin = request.POST.get('show_gstin') == 'on'
            inv.show_hsn = request.POST.get('show_hsn') == 'on'
            inv.show_discount = request.POST.get('show_discount') == 'on'
            inv.show_payment_details = request.POST.get('show_payment_details') == 'on'
            inv.save()
            messages.success(request, "Invoice Settings updated successfully.")

        elif section == 'currency':
            curr = all_settings['currency']
            curr.currency_code = request.POST.get('currency_code', curr.currency_code)
            curr.currency_symbol = request.POST.get('currency_symbol', curr.currency_symbol)
            curr.country = request.POST.get('country', curr.country)
            curr.timezone = request.POST.get('timezone', curr.timezone)
            curr.date_format = request.POST.get('date_format', curr.date_format)
            curr.save()
            messages.success(request, "Currency & Regional Settings updated successfully.")

        elif section == 'warehouse':
            wh = all_settings['warehouse']
            wh.allow_multiple_warehouses = request.POST.get('allow_multiple_warehouses') == 'on'
            wh.allow_warehouse_transfer = request.POST.get('allow_warehouse_transfer') == 'on'
            wh.require_transfer_approval = request.POST.get('require_transfer_approval') == 'on'
            wh.allow_negative_stock = request.POST.get('allow_negative_stock') == 'on'
            wh.save()
            messages.success(request, "Warehouse Configuration updated successfully.")

        elif section == 'inventory':
            inv_cfg = all_settings['inventory']
            inv_cfg.valuation_method = request.POST.get('valuation_method', inv_cfg.valuation_method)
            inv_cfg.low_stock_threshold_default = request.POST.get('low_stock_threshold_default', inv_cfg.low_stock_threshold_default)
            inv_cfg.batch_tracking = request.POST.get('batch_tracking') == 'on'
            inv_cfg.expiry_tracking = request.POST.get('expiry_tracking') == 'on'
            inv_cfg.serial_number_tracking = request.POST.get('serial_number_tracking') == 'on'
            inv_cfg.barcode_tracking = request.POST.get('barcode_tracking') == 'on'
            inv_cfg.qr_code_tracking = request.POST.get('qr_code_tracking') == 'on'
            inv_cfg.save()
            messages.success(request, "Inventory Configuration updated successfully.")

        elif section == 'purchase':
            pur = all_settings['purchase']
            pur.purchase_order_required = request.POST.get('purchase_order_required') == 'on'
            pur.purchase_approval_required = request.POST.get('purchase_approval_required') == 'on'
            pur.goods_receipt_required = request.POST.get('goods_receipt_required') == 'on'
            pur.allow_partial_receiving = request.POST.get('allow_partial_receiving') == 'on'
            pur.duplicate_invoice_detection = request.POST.get('duplicate_invoice_detection') == 'on'
            pur.default_payment_terms = request.POST.get('default_payment_terms', pur.default_payment_terms)
            pur.save()
            messages.success(request, "Purchase Configuration updated successfully.")

        elif section == 'ocr':
            ocr = all_settings['ocr']
            ocr.provider = request.POST.get('provider', ocr.provider)
            new_api_key = request.POST.get('api_key')
            if new_api_key and not new_api_key.startswith('***'):
                # Mask stored API key
                ocr.api_key_masked = new_api_key[:6] + '*' * 16 + new_api_key[-4:] if len(new_api_key) > 10 else '***MASKED***'
            ocr.model_name = request.POST.get('model_name', ocr.model_name)
            ocr.confidence_threshold = request.POST.get('confidence_threshold', ocr.confidence_threshold)
            ocr.save()
            messages.success(request, "OCR & AI Engine Settings updated successfully.")

        elif section == 'notification':
            notif = all_settings['notification']
            notif.notify_low_stock = request.POST.get('notify_low_stock') == 'on'
            notif.notify_out_of_stock = request.POST.get('notify_out_of_stock') == 'on'
            notif.notify_purchase_created = request.POST.get('notify_purchase_created') == 'on'
            notif.notify_stock_transfer = request.POST.get('notify_stock_transfer') == 'on'
            notif.channel_email = request.POST.get('channel_email') == 'on'
            notif.channel_in_app = request.POST.get('channel_in_app') == 'on'
            notif.save()
            messages.success(request, "Notification Preferences updated successfully.")

        elif section == 'security':
            sec = all_settings['security']
            sec.session_timeout_minutes = request.POST.get('session_timeout_minutes', sec.session_timeout_minutes)
            sec.password_min_length = request.POST.get('password_min_length', sec.password_min_length)
            sec.max_login_attempts = request.POST.get('max_login_attempts', sec.max_login_attempts)
            sec.require_strong_password = request.POST.get('require_strong_password') == 'on'
            sec.save()
            messages.success(request, "Security Policy Settings updated successfully.")

        elif section == 'preferences':
            pref = all_settings['preferences']
            pref.theme = request.POST.get('theme', pref.theme)
            pref.items_per_page = request.POST.get('items_per_page', pref.items_per_page)
            pref.compact_table_mode = request.POST.get('compact_table_mode') == 'on'
            pref.enable_animations = request.POST.get('enable_animations') == 'on'
            pref.save()
            messages.success(request, "System Preferences updated successfully.")

        RBACService.log_activity(request.user, f"Updated System Settings section '{section}'", "Settings", request=request)
        return redirect(f'/settings/?section={section}')
