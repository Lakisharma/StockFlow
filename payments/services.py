from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from sales.models import Customer, SalesInvoice
from suppliers.models import Supplier
from purchases.models import Purchase
from notifications.services import NotificationService
from users.services import RBACService
from .models import PaymentAccount, Payment, PaymentAllocation

class FinanceService:

    @classmethod
    def generate_payment_number(cls):
        year_str = timezone.now().strftime('%Y')
        count = Payment.objects.count() + 1
        while True:
            candidate = f"PAY-{year_str}-{count:04d}"
            if not Payment.objects.filter(payment_number=candidate).exists():
                return candidate
            count += 1

    @classmethod
    @transaction.atomic
    def process_customer_payment(cls, customer, sales_invoice, amount, method, account, ref, user, notes=''):
        amt = Decimal(str(amount))
        payment_no = cls.generate_payment_number()

        payment = Payment.objects.create(
            payment_number=payment_no,
            payment_date=timezone.now().date(),
            payment_type='customer_payment',
            customer=customer,
            sales_invoice=sales_invoice,
            amount=amt,
            payment_method=method,
            reference_number=ref,
            account=account,
            notes=notes,
            status='completed',
            created_by=user
        )

        if sales_invoice:
            sales_invoice.paid_amount = Decimal(str(sales_invoice.paid_amount or 0)) + amt
            if sales_invoice.paid_amount >= sales_invoice.grand_total:
                sales_invoice.payment_status = 'paid'
            elif sales_invoice.paid_amount > 0:
                sales_invoice.payment_status = 'partial'
            sales_invoice.save()

            PaymentAllocation.objects.create(
                payment=payment,
                sales_invoice=sales_invoice,
                allocated_amount=amt
            )

        if customer:
            customer.outstanding_amount = max(Decimal(str(customer.outstanding_amount or 0)) - amt, Decimal('0.00'))
            customer.save()

        if account:
            account.current_balance = Decimal(str(account.current_balance or 0)) + amt
            account.save()

        RBACService.log_activity(user, f"Recorded Customer Payment '{payment.payment_number}' of ₹{amt:,.2f} for Customer '{customer.name if customer else 'General'}'", "Finance", reference=payment.payment_number)

        NotificationService.notify_user(
            user=user,
            title=f"Payment Received: {payment.payment_number}",
            message=f"Received ₹{amt:,.2f} from {customer.name if customer else 'Customer'}.",
            notification_type='system_alert',
            priority='normal',
            module='Finance',
            action_url=f"/payments/transactions/{payment.id}/",
            record_type='Payment',
            record_id=payment.id
        )
        return payment

    @classmethod
    @transaction.atomic
    def process_supplier_payment(cls, supplier, purchase, amount, method, account, ref, user, notes=''):
        amt = Decimal(str(amount))
        payment_no = cls.generate_payment_number()

        payment = Payment.objects.create(
            payment_number=payment_no,
            payment_date=timezone.now().date(),
            payment_type='supplier_payment',
            supplier=supplier,
            purchase=purchase,
            amount=amt,
            payment_method=method,
            reference_number=ref,
            account=account,
            notes=notes,
            status='completed',
            created_by=user
        )

        if purchase:
            purchase.paid_amount = Decimal(str(purchase.paid_amount or 0)) + amt
            if purchase.paid_amount >= purchase.grand_total:
                purchase.payment_status = 'paid'
            elif purchase.paid_amount > 0:
                purchase.payment_status = 'partial'
            purchase.save()

            PaymentAllocation.objects.create(
                payment=payment,
                purchase=purchase,
                allocated_amount=amt
            )

        if supplier:
            supplier.outstanding_balance = max(Decimal(str(supplier.outstanding_balance or 0)) - amt, Decimal('0.00'))
            supplier.save()

        if account:
            account.current_balance = Decimal(str(account.current_balance or 0)) - amt
            account.save()

        RBACService.log_activity(user, f"Recorded Supplier Payment '{payment.payment_number}' of ₹{amt:,.2f} to Supplier '{supplier.name if supplier else 'General'}'", "Finance", reference=payment.payment_number)
        return payment

    @classmethod
    @transaction.atomic
    def reverse_payment(cls, payment, user, reason):
        if payment.status == 'reversed':
            return True

        amt = Decimal(str(payment.amount))

        if payment.payment_type == 'customer_payment':
            if payment.sales_invoice:
                payment.sales_invoice.paid_amount = max(Decimal(str(payment.sales_invoice.paid_amount or 0)) - amt, Decimal('0.00'))
                if payment.sales_invoice.paid_amount == 0:
                    payment.sales_invoice.payment_status = 'unpaid'
                else:
                    payment.sales_invoice.payment_status = 'partial'
                payment.sales_invoice.save()

            if payment.customer:
                payment.customer.outstanding_amount += amt
                payment.customer.save()

            if payment.account:
                payment.account.current_balance -= amt
                payment.account.save()

        elif payment.payment_type == 'supplier_payment':
            if payment.purchase:
                payment.purchase.paid_amount = max(Decimal(str(payment.purchase.paid_amount or 0)) - amt, Decimal('0.00'))
                if payment.purchase.paid_amount == 0:
                    payment.purchase.payment_status = 'unpaid'
                else:
                    payment.purchase.payment_status = 'partial'
                payment.purchase.save()

            if payment.supplier:
                payment.supplier.outstanding_balance += amt
                payment.supplier.save()

            if payment.account:
                payment.account.current_balance += amt
                payment.account.save()

        payment.status = 'reversed'
        payment.reversal_reason = reason
        payment.save()

        RBACService.log_activity(user, f"Reversed Payment '{payment.payment_number}' of ₹{amt:,.2f}. Reason: {reason}", "Finance", reference=payment.payment_number)
        return True

    @classmethod
    def get_customer_ledger(cls, customer):
        entries = []
        running_bal = Decimal('0.00')

        invoices = SalesInvoice.objects.filter(customer=customer).order_by('invoice_date', 'created_at')
        payments = Payment.objects.filter(customer=customer, status='completed').order_by('payment_date', 'created_at')

        # Combine chronologically
        combined = []
        for inv in invoices:
            combined.append({'date': inv.invoice_date, 'ref': inv.invoice_number, 'type': 'Invoice', 'debit': inv.grand_total, 'credit': Decimal('0.00')})
        for pay in payments:
            combined.append({'date': pay.payment_date, 'ref': pay.payment_number, 'type': 'Payment', 'debit': Decimal('0.00'), 'credit': pay.amount})

        combined.sort(key=lambda x: x['date'])

        for item in combined:
            running_bal += item['debit'] - item['credit']
            item['balance'] = running_bal
            entries.append(item)

        return entries

    @classmethod
    def get_aging_report(cls):
        today = timezone.now().date()
        receivables_aging = {'current': 0, '1_30': 0, '31_60': 0, '61_90': 0, 'over_90': 0, 'total': 0}

        unpaid_invoices = SalesInvoice.objects.exclude(payment_status='paid')
        for inv in unpaid_invoices:
            due = inv.grand_total - inv.paid_amount
            days = (today - inv.invoice_date).days
            receivables_aging['total'] += due

            if days <= 0:
                receivables_aging['current'] += due
            elif days <= 30:
                receivables_aging['1_30'] += due
            elif days <= 60:
                receivables_aging['31_60'] += due
            elif days <= 90:
                receivables_aging['61_90'] += due
            else:
                receivables_aging['over_90'] += due

        return receivables_aging
