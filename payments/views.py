from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal
from sales.models import Customer, SalesInvoice
from suppliers.models import Supplier
from purchases.models import Purchase
from .models import PaymentAccount, Payment, PaymentAllocation
from .services import FinanceService

class FinanceDashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        total_receivables = Customer.objects.aggregate(total=Sum('outstanding_amount'))['total'] or Decimal('0.00')
        total_payables = Supplier.objects.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')

        today = timezone.now().date()
        rec_today = Payment.objects.filter(payment_type='customer_payment', payment_date=today, status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        paid_today = Payment.objects.filter(payment_type='supplier_payment', payment_date=today, status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        recent_payments = Payment.objects.select_related('customer', 'supplier', 'account')[:10]
        accounts = PaymentAccount.objects.all()

        context = {
            'total_receivables': total_receivables,
            'total_payables': total_payables,
            'rec_today': rec_today,
            'paid_today': paid_today,
            'recent_payments': recent_payments,
            'accounts': accounts,
            'active_menu': 'finance'
        }
        return render(request, 'payments/dashboard.html', context)

class ReceivablesListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = SalesInvoice.objects.select_related('customer', 'warehouse').exclude(payment_status='paid')
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(invoice_number__icontains=search) | Q(customer__name__icontains=search))

        today = timezone.now().date()
        receivables_list = []
        for inv in qs:
            outstanding = inv.grand_total - inv.paid_amount
            days_overdue = max((today - inv.invoice_date).days, 0)
            receivables_list.append({
                'invoice': inv,
                'outstanding': outstanding,
                'days_overdue': days_overdue
            })

        context = {
            'receivables': receivables_list,
            'search': search,
            'active_menu': 'finance'
        }
        return render(request, 'payments/receivables_list.html', context)

class PayablesListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = Purchase.objects.select_related('supplier', 'warehouse').exclude(payment_status='paid')
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(invoice_number__icontains=search) | Q(supplier__name__icontains=search))

        today = timezone.now().date()
        payables_list = []
        for pur in qs:
            outstanding = pur.grand_total - pur.paid_amount
            days_overdue = max((today - pur.purchase_date).days, 0)
            payables_list.append({
                'purchase': pur,
                'outstanding': outstanding,
                'days_overdue': days_overdue
            })

        context = {
            'payables': payables_list,
            'search': search,
            'active_menu': 'finance'
        }
        return render(request, 'payments/payables_list.html', context)

class PaymentListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = Payment.objects.select_related('customer', 'supplier', 'account', 'created_by').all()
        search = request.GET.get('search')
        type_filter = request.GET.get('type')

        if search:
            qs = qs.filter(Q(payment_number__icontains=search) | Q(reference_number__icontains=search) | Q(customer__name__icontains=search) | Q(supplier__name__icontains=search))
        if type_filter:
            qs = qs.filter(payment_type=type_filter)

        context = {
            'payments': qs[:100],
            'search': search,
            'type_filter': type_filter,
            'active_menu': 'finance'
        }
        return render(request, 'payments/payment_list.html', context)

class PaymentCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        customers = Customer.objects.filter(status='active')
        suppliers = Supplier.objects.filter(status='active')
        accounts = PaymentAccount.objects.filter(status='active')

        # Pre-selected invoice or purchase
        inv_id = request.GET.get('invoice')
        pur_id = request.GET.get('purchase')

        sel_invoice = get_object_or_404(SalesInvoice, pk=inv_id) if inv_id else None
        sel_purchase = get_object_or_404(Purchase, pk=pur_id) if pur_id else None

        context = {
            'auto_payment_number': FinanceService.generate_payment_number(),
            'customers': customers,
            'suppliers': suppliers,
            'accounts': accounts,
            'sel_invoice': sel_invoice,
            'sel_purchase': sel_purchase,
            'active_menu': 'finance'
        }
        return render(request, 'payments/payment_create.html', context)

    def post(self, request):
        payment_type = request.POST.get('payment_type')
        customer_id = request.POST.get('customer')
        supplier_id = request.POST.get('supplier')
        invoice_id = request.POST.get('invoice')
        purchase_id = request.POST.get('purchase')
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method', 'bank_transfer')
        account_id = request.POST.get('account')
        ref = request.POST.get('reference_number', '')
        notes = request.POST.get('notes', '')

        cust = Customer.objects.filter(pk=customer_id).first() if customer_id else None
        supp = Supplier.objects.filter(pk=supplier_id).first() if supplier_id else None
        inv = SalesInvoice.objects.filter(pk=invoice_id).first() if invoice_id else None
        pur = Purchase.objects.filter(pk=purchase_id).first() if purchase_id else None
        acc = PaymentAccount.objects.filter(pk=account_id).first() if account_id else None

        if payment_type == 'customer_payment':
            pay = FinanceService.process_customer_payment(cust, inv, amount, method, acc, ref, request.user, notes)
            messages.success(request, f"Customer Payment '{pay.payment_number}' of ₹{pay.amount:,.2f} recorded successfully.")
        elif payment_type == 'supplier_payment':
            pay = FinanceService.process_supplier_payment(supp, pur, amount, method, acc, ref, request.user, notes)
            messages.success(request, f"Supplier Payment '{pay.payment_number}' of ₹{pay.amount:,.2f} recorded successfully.")
        else:
            messages.error(request, "Invalid payment type specified.")
            return redirect('payment-list')

        return redirect('payment-detail', pk=pay.id)

class PaymentDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        payment = get_object_or_404(Payment.objects.select_related('customer', 'supplier', 'account', 'sales_invoice', 'purchase', 'created_by'), pk=pk)
        return render(request, 'payments/payment_detail.html', {'payment': payment, 'active_menu': 'finance'})

class PaymentReverseView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        payment = get_object_or_404(Payment, pk=pk)
        reason = request.POST.get('reversal_reason', 'Reversed by admin')
        FinanceService.reverse_payment(payment, request.user, reason)
        messages.success(request, f"Payment '{payment.payment_number}' has been reversed successfully.")
        return redirect('payment-detail', pk=payment.id)

class PaymentPrintView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        payment = get_object_or_404(Payment.objects.select_related('customer', 'supplier', 'account', 'sales_invoice', 'purchase'), pk=pk)
        return render(request, 'payments/payment_receipt.html', {'payment': payment})

class CustomerLedgerView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        customers = Customer.objects.all()
        selected_cust_id = request.GET.get('customer')
        selected_customer = Customer.objects.filter(pk=selected_cust_id).first() if selected_cust_id else customers.first()

        ledger_entries = FinanceService.get_customer_ledger(selected_customer) if selected_customer else []

        context = {
            'customers': customers,
            'selected_customer': selected_customer,
            'ledger_entries': ledger_entries,
            'active_menu': 'finance'
        }
        return render(request, 'payments/ledger_view.html', context)

class AgingReportView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        aging_data = FinanceService.get_aging_report()
        context = {
            'aging_data': aging_data,
            'active_menu': 'finance'
        }
        return render(request, 'payments/aging_report.html', context)
