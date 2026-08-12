import datetime
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from audit_logs.services import AuditLogService
from notifications.services import NotificationService
from .models import Department, Designation, Shift, Employee, Attendance, LeaveType, LeaveRequest, Holiday

DEFAULT_DEPARTMENTS = [
    ('Warehouse & Logistics', 'Operations and stock management'),
    ('Purchasing & Procurement', 'Supplier orders and inventory buying'),
    ('Sales & Dispatch', 'Customer orders, sales, and delivery'),
    ('Finance & Accounts', 'Billing, payments, and financial management'),
    ('Management & HR', 'Administration, staff management, and strategy'),
    ('IT & Systems', 'System administration and software technical support'),
]

DEFAULT_DESIGNATIONS = [
    ('Warehouse Manager', 'Manages warehouse operations and inventory team'),
    ('Warehouse Operator', 'Stock movement, loading, and barcode scanning'),
    ('Data Entry Operator', 'Data entry for inventory and invoices'),
    ('Accountant', 'Payment recording and ledger bookkeeping'),
    ('Purchase Executive', 'Purchase order creation and supplier coordination'),
    ('Sales Executive', 'Sales order creation and customer accounts'),
    ('Operations Supervisor', 'Supervises daily warehouse and dispatch tasks'),
    ('System Admin', 'Full system access and user management'),
]

DEFAULT_SHIFTS = [
    ('Morning Shift', datetime.time(9, 0), datetime.time(18, 0), 15, 60),
    ('Evening Shift', datetime.time(14, 0), datetime.time(23, 0), 15, 60),
    ('Night Shift', datetime.time(22, 0), datetime.time(7, 0), 15, 60),
]

DEFAULT_LEAVE_TYPES = [
    ('Casual Leave', 'CL', 12),
    ('Sick Leave', 'SL', 10),
    ('Earned Leave', 'EL', 15),
    ('Emergency Leave', 'EML', 5),
    ('Unpaid Leave', 'LWP', 0),
]

class EmployeeService:

    @classmethod
    def seed_default_org_data(cls):
        for name, desc in DEFAULT_DEPARTMENTS:
            Department.objects.get_or_create(name=name, defaults={'description': desc, 'status': 'active'})

        wh_dept = Department.objects.filter(name='Warehouse & Logistics').first()
        for name, desc in DEFAULT_DESIGNATIONS:
            Designation.objects.get_or_create(name=name, defaults={'department': wh_dept, 'description': desc})

        for name, st, et, grace, brk in DEFAULT_SHIFTS:
            Shift.objects.get_or_create(name=name, defaults={'start_time': st, 'end_time': et, 'grace_period_mins': grace, 'break_duration_mins': brk})

        for name, code, days in DEFAULT_LEAVE_TYPES:
            LeaveType.objects.get_or_create(name=name, defaults={'code': code, 'default_days_per_year': days})

    @classmethod
    def generate_employee_code(cls):
        count = Employee.objects.count() + 1
        while True:
            candidate = f"EMP-{count:04d}"
            if not Employee.objects.filter(employee_code=candidate).exists():
                return candidate
            count += 1

    @classmethod
    def record_check_in(cls, employee, date=None, check_in_time=None, warehouse=None, source='web', user=None):
        if not date:
            date = timezone.now().date()
        if not check_in_time:
            check_in_time = timezone.now().time()

        existing = Attendance.objects.filter(employee=employee, date=date).first()
        if existing and existing.check_in:
            raise ValueError("Today's attendance has already been recorded.")

        late_mins = 0
        status = 'present'

        if employee.shift:
            shift_start = employee.shift.start_time
            shift_start_dt = datetime.datetime.combine(date, shift_start)
            check_in_dt = datetime.datetime.combine(date, check_in_time)
            grace_cutoff = shift_start_dt + datetime.timedelta(minutes=employee.shift.grace_period_mins)

            if check_in_dt > grace_cutoff:
                late_mins = int((check_in_dt - shift_start_dt).total_seconds() // 60)
                status = 'late'

        att, _ = Attendance.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'check_in': check_in_time,
                'status': status,
                'late_minutes': late_mins,
                'warehouse': warehouse or employee.primary_warehouse,
                'source': source,
                'created_by': user
            }
        )

        if not att.check_in:
            att.check_in = check_in_time
            att.status = status
            att.late_minutes = late_mins
            att.save()

        return att

    @classmethod
    def record_check_out(cls, employee, date=None, check_out_time=None):
        if not date:
            date = timezone.now().date()
        if not check_out_time:
            check_out_time = timezone.now().time()

        att = Attendance.objects.filter(employee=employee, date=date).first()
        if not att or not att.check_in:
            raise ValueError("Cannot check out without a valid check-in record for today.")

        att.check_out = check_out_time

        in_dt = datetime.datetime.combine(date, att.check_in)
        out_dt = datetime.datetime.combine(date, check_out_time)

        if out_dt < in_dt:
            out_dt += datetime.timedelta(days=1)

        total_secs = (out_dt - in_dt).total_seconds()
        work_hours = Decimal(str(round(total_secs / 3600.0, 2)))

        # Overtime calculation
        overtime = Decimal('0.00')
        if employee.shift:
            shift_end = employee.shift.end_time
            shift_end_dt = datetime.datetime.combine(date, shift_end)
            if out_dt > shift_end_dt + datetime.timedelta(minutes=30):
                ot_secs = (out_dt - shift_end_dt).total_seconds()
                overtime = Decimal(str(round(ot_secs / 3600.0, 2)))

        att.working_hours = work_hours
        att.overtime_hours = overtime
        att.save()
        return att

    @classmethod
    @transaction.atomic
    def approve_leave(cls, leave_request, user, remarks=""):
        leave_request.status = 'approved'
        leave_request.approved_by = user
        leave_request.save()

        # Update Attendance for date range
        curr = leave_request.start_date
        while curr <= leave_request.end_date:
            att, _ = Attendance.objects.get_or_create(
                employee=leave_request.employee,
                date=curr,
                defaults={'status': 'leave', 'remarks': f"Leave: {leave_request.leave_type.name}"}
            )
            att.status = 'leave'
            att.remarks = f"Leave: {leave_request.leave_type.name}"
            att.save()
            curr += datetime.timedelta(days=1)

        # Audit Log & Notification
        AuditLogService.log_event(user, 'APPROVE_LEAVE', 'Employee', record_type='Employee', record_id=leave_request.employee.id, description=f"Approved leave request for {leave_request.employee.full_name} ({leave_request.start_date} to {leave_request.end_date})")
        if leave_request.employee.user:
            NotificationService.create_notification(
                user=leave_request.employee.user,
                title="Leave Approved",
                message=f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been approved.",
                notification_type='info'
            )
        return leave_request

    @classmethod
    def get_attendance_summary_today(cls):
        today = timezone.now().date()
        total_active = Employee.objects.filter(status='active').count()
        today_atts = Attendance.objects.filter(date=today)

        present = today_atts.filter(status__in=['present', 'late']).count()
        late = today_atts.filter(status='late').count()
        on_leave = today_atts.filter(status='leave').count()
        absent = max(total_active - (present + on_leave), 0)

        return {
            'total_active': total_active,
            'present': present,
            'late': late,
            'on_leave': on_leave,
            'absent': absent,
        }
