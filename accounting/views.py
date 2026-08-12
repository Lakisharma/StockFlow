from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal
from payments.models import PaymentAccount
from products.models import Warehouse, Product, WarehouseStock
from sales.models import SalesInvoice, SalesOrderItem
from purchases.models import Purchase
from .models import ExpenseCategory, Expense
from .services import AccountingService

class AccountingDashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        fin_data = AccountingService.get_financial_dashboard_data()
        cash_data = AccountingService.get_cash_flow()
        tax_data = AccountingService.get_tax_summary()

        context = {
            'fin': fin_data,
            'cash': cash_data,
            'tax': tax_data,
            'active_menu': 'accounting'
        }
        return render(request, 'accounting/dashboard.html', context)

class ProfitAndLossView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        fin = AccountingService.get_financial_dashboard_data()
        return render(request, 'accounting/profit_loss.html', {'fin': fin, 'active_menu': 'accounting'})

class CashFlowView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        cash = AccountingService.get_cash_flow()
        return render(request, 'accounting/cash_flow.html', {'cash': cash, 'active_menu': 'accounting'})

class TaxSummaryView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        tax = AccountingService.get_tax_summary()
        return render(request, 'accounting/tax_summary.html', {'tax': tax, 'active_menu': 'accounting'})

class InventoryValuationView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        valuation_list = []
        total_val = Decimal('0.00')

        stocks = WarehouseStock.objects.select_related('product', 'warehouse').filter(quantity__gt=0)
        for s in stocks:
            unit_cost = s.product.purchase_price or Decimal('0.00')
            line_val = s.quantity * unit_cost
            total_val += line_val
            valuation_list.append({
                'product': s.product,
                'warehouse': s.warehouse,
                'quantity': s.quantity,
                'unit_cost': unit_cost,
                'total_value': line_val
            })

        context = {
            'valuations': valuation_list,
            'total_val': total_val,
            'active_menu': 'accounting'
        }
        return render(request, 'accounting/inventory_valuation.html', context)

class ExpenseListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        qs = Expense.objects.select_related('category', 'account', 'warehouse', 'created_by').all()
        search = request.GET.get('search')
        if search:
            qs = qs.filter(Q(expense_number__icontains=search) | Q(description__icontains=search) | Q(category__name__icontains=search))

        categories = ExpenseCategory.objects.filter(status='active')
        total_expenses = Expense.objects.filter(status__in=['approved', 'paid']).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        context = {
            'expenses': qs[:100],
            'categories': categories,
            'total_expenses': total_expenses,
            'search': search,
            'active_menu': 'accounting'
        }
        return render(request, 'accounting/expense_list.html', context)

class ExpenseCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        AccountingService.seed_default_expense_categories()
        categories = ExpenseCategory.objects.filter(status='active')
        accounts = PaymentAccount.objects.filter(status='active')
        warehouses = Warehouse.objects.filter(status='active')

        context = {
            'auto_expense_number': AccountingService.generate_expense_number(),
            'categories': categories,
            'accounts': accounts,
            'warehouses': warehouses,
            'active_menu': 'accounting'
        }
        return render(request, 'accounting/expense_create.html', context)

    def post(self, request):
        expense_date = request.POST.get('expense_date') or timezone.now().date()
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method', 'bank_transfer')
        account_id = request.POST.get('account')
        warehouse_id = request.POST.get('warehouse')
        ref = request.POST.get('reference_number', '')
        notes = request.POST.get('notes', '')

        cat = get_object_or_404(ExpenseCategory, pk=category_id)
        acc = PaymentAccount.objects.filter(pk=account_id).first() if account_id else None
        wh = Warehouse.objects.filter(pk=warehouse_id).first() if warehouse_id else None
        amt = Decimal(str(amount))

        exp = Expense.objects.create(
            expense_number=AccountingService.generate_expense_number(),
            expense_date=expense_date,
            category=cat,
            description=description,
            amount=amt,
            payment_method=method,
            account=acc,
            warehouse=wh,
            reference_number=ref,
            notes=notes,
            status='paid',
            created_by=request.user
        )

        # Deduct Account balance if paid
        if acc:
            acc.current_balance = max(Decimal(str(acc.current_balance or 0)) - amt, Decimal('0.00'))
            acc.save()

        messages.success(request, f"Expense '{exp.expense_number}' of ₹{exp.amount:,.2f} recorded successfully.")
        return redirect('expense-list')

class ProductProfitabilityView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        prof_list = []
        products = Product.objects.all()

        for p in products:
            items = SalesOrderItem.objects.filter(product=p, sales_order__status__in=['dispatched', 'completed'])
            units_sold = items.aggregate(total=Sum('dispatched_quantity'))['total'] or 0
            if units_sold <= 0:
                continue

            revenue = sum(i.dispatched_quantity * i.rate for i in items)
            cost = units_sold * (p.purchase_price or Decimal('0.00'))
            profit = revenue - cost
            margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0

            prof_list.append({
                'product': p,
                'units_sold': units_sold,
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin_pct': margin_pct
            })

        context = {
            'product_profitability': prof_list,
            'active_menu': 'accounting'
        }
        return render(request, 'accounting/product_profitability.html', context)
