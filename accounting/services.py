from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, F
from sales.models import SalesInvoice, SalesOrderItem, Customer
from purchases.models import Purchase, PurchaseItem
from suppliers.models import Supplier
from products.models import Product, WarehouseStock
from payments.models import PaymentAccount, Payment
from .models import ExpenseCategory, Expense

DEFAULT_EXPENSE_CATEGORIES = [
    ('Rent', 'RENT', 'Office and warehouse rental expenses'),
    ('Electricity & Utilities', 'UTIL', 'Electricity, water, and power charges'),
    ('Internet & Telecom', 'TELE', 'Broadband, mobile, and communication charges'),
    ('Salaries & Wages', 'PAYROLL', 'Staff salaries, wages, and bonuses'),
    ('Transport & Freight', 'FREIGHT', 'Logistics, delivery, and courier charges'),
    ('Office Supplies', 'SUPPLIES', 'Stationery, printing, and general supplies'),
    ('Maintenance & Repairs', 'MAINT', 'Equipment and warehouse maintenance'),
    ('Packaging Materials', 'PACK', 'Boxes, tape, and packing supplies'),
    ('Marketing & Advertising', 'MKT', 'Promotions, ads, and brand marketing'),
    ('Travel & Conveyance', 'TRAVEL', 'Staff travel and local transport'),
    ('Professional Fees', 'PROF', 'Legal, accounting, and consulting fees'),
    ('Other Expenses', 'MISC', 'Miscellaneous operational expenses')
]

class AccountingService:

    @classmethod
    def seed_default_expense_categories(cls):
        for name, code, desc in DEFAULT_EXPENSE_CATEGORIES:
            ExpenseCategory.objects.get_or_create(name=name, defaults={'code': code, 'description': desc, 'status': 'active'})

    @classmethod
    def generate_expense_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = Expense.objects.count() + 1
        while True:
            candidate = f"EXP-{year_str}-{count:04d}"
            if not Expense.objects.filter(expense_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def get_financial_dashboard_data(cls, start_date=None, end_date=None):
        cls.seed_default_expense_categories()

        inv_qs = SalesInvoice.objects.exclude(status='cancelled')
        pur_qs = Purchase.objects.exclude(status='cancelled')
        exp_qs = Expense.objects.filter(status__in=['approved', 'paid'])

        if start_date:
            inv_qs = inv_qs.filter(invoice_date__gte=start_date)
            pur_qs = pur_qs.filter(purchase_date__gte=start_date)
            exp_qs = exp_qs.filter(expense_date__gte=start_date)

        if end_date:
            inv_qs = inv_qs.filter(invoice_date__lte=end_date)
            pur_qs = pur_qs.filter(purchase_date__lte=end_date)
            exp_qs = exp_qs.filter(expense_date__lte=end_date)

        # Revenue
        gross_revenue = inv_qs.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        output_tax = inv_qs.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
        net_sales = gross_revenue - output_tax

        # Cost of Goods Sold (COGS)
        cogs = Decimal('0.00')
        so_items = SalesOrderItem.objects.filter(sales_order__in=[inv.sales_order for inv in inv_qs if inv.sales_order])
        for item in so_items:
            cogs += (item.ordered_quantity * (item.product.purchase_price or Decimal('0.00')))

        # Purchases
        total_purchases = pur_qs.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        input_tax = pur_qs.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')

        # Expenses
        total_expenses = exp_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Profits
        gross_profit = net_sales - cogs
        net_profit = gross_profit - total_expenses

        # Margins
        gross_margin_pct = (gross_profit / net_sales * 100) if net_sales > 0 else 0.0
        net_margin_pct = (net_profit / net_sales * 100) if net_sales > 0 else 0.0

        # Outstanding & Balances
        total_receivables = Customer.objects.aggregate(total=Sum('outstanding_amount'))['total'] or Decimal('0.00')
        total_payables = Supplier.objects.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')

        accounts = PaymentAccount.objects.all()
        cash_balance = accounts.filter(account_type='cash').aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
        bank_balance = accounts.filter(account_type='bank').aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')

        # Inventory Value
        inventory_value = Decimal('0.00')
        for ws in WarehouseStock.objects.select_related('product').all():
            inventory_value += (ws.quantity * (ws.product.purchase_price or Decimal('0.00')))

        return {
            'gross_revenue': gross_revenue,
            'net_sales': net_sales,
            'output_tax': output_tax,
            'cogs': cogs,
            'total_purchases': total_purchases,
            'input_tax': input_tax,
            'total_expenses': total_expenses,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'gross_margin_pct': gross_margin_pct,
            'net_margin_pct': net_margin_pct,
            'total_receivables': total_receivables,
            'total_payables': total_payables,
            'cash_balance': cash_balance,
            'bank_balance': bank_balance,
            'inventory_value': inventory_value,
        }

    @classmethod
    def get_cash_flow(cls, start_date=None, end_date=None):
        payments_qs = Payment.objects.filter(status='completed')
        expenses_qs = Expense.objects.filter(status='paid')

        if start_date:
            payments_qs = payments_qs.filter(payment_date__gte=start_date)
            expenses_qs = expenses_qs.filter(expense_date__gte=start_date)
        if end_date:
            payments_qs = payments_qs.filter(payment_date__lte=end_date)
            expenses_qs = expenses_qs.filter(expense_date__lte=end_date)

        customer_inflow = payments_qs.filter(payment_type='customer_payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        supplier_outflow = payments_qs.filter(payment_type='supplier_payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        expense_outflow = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_inflow = customer_inflow
        total_outflow = supplier_outflow + expense_outflow
        net_cash_flow = total_inflow - total_outflow

        return {
            'customer_inflow': customer_inflow,
            'supplier_outflow': supplier_outflow,
            'expense_outflow': expense_outflow,
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'net_cash_flow': net_cash_flow,
        }

    @classmethod
    def get_tax_summary(cls, start_date=None, end_date=None):
        inv_qs = SalesInvoice.objects.exclude(status='cancelled')
        pur_qs = Purchase.objects.exclude(status='cancelled')

        if start_date:
            inv_qs = inv_qs.filter(invoice_date__gte=start_date)
            pur_qs = pur_qs.filter(purchase_date__gte=start_date)
        if end_date:
            inv_qs = inv_qs.filter(invoice_date__lte=end_date)
            pur_qs = pur_qs.filter(purchase_date__lte=end_date)

        output_tax = inv_qs.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
        input_tax = pur_qs.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
        net_tax_liability = output_tax - input_tax

        return {
            'output_tax': output_tax,
            'input_tax': input_tax,
            'cgst_output': output_tax / Decimal('2.0'),
            'sgst_output': output_tax / Decimal('2.0'),
            'cgst_input': input_tax / Decimal('2.0'),
            'sgst_input': input_tax / Decimal('2.0'),
            'net_tax_liability': net_tax_liability,
        }
