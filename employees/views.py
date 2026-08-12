import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from products.models import Warehouse
from .models import Department, Designation, Shift, Employee, Attendance, LeaveType, LeaveRequest, Holiday
from .services import EmployeeService

class EmployeeListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        EmployeeService.seed_default_org_data()
        qs = Employee.objects.select_related('department', 'designation', 'primary_warehouse', 'shift', 'user').all()

        search = request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(employee_code__icontains=search) |
                Q(full_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(department__name__icontains=search)
            )

        context = {
            'employees': qs[:100],
            'departments': Department.objects.filter(status='active'),
            'search': search,
            'active_menu': 'employees'
        }
        return render(request, 'employees/employee_list.html', context)

class EmployeeCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        EmployeeService.seed_default_org_data()
        context = {
            'auto_code': EmployeeService.generate_employee_code(),
            'departments': Department.objects.filter(status='active'),
            'designations': Designation.objects.all(),
            'shifts': Shift.objects.filter(status='active'),
            'warehouses': Warehouse.objects.filter(status='active'),
            'users': User.objects.filter(employee_profile__isnull=True),
            'active_menu': 'employees'
        }
        return render(request, 'employees/employee_create.html', context)

    def post(self, request):
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        dob = request.POST.get('date_of_birth') or None
        joining_date = request.POST.get('joining_date') or timezone.now().date()
        dept_id = request.POST.get('department')
        desig_id = request.POST.get('designation')
        wh_id = request.POST.get('primary_warehouse')
        shift_id = request.POST.get('shift')
        user_id = request.POST.get('user')
        address = request.POST.get('address', '')
        emergency = request.POST.get('emergency_contact', '')
        notes = request.POST.get('notes', '')

        dept = Department.objects.filter(pk=dept_id).first() if dept_id else None
        desig = Designation.objects.filter(pk=desig_id).first() if desig_id else None
        wh = Warehouse.objects.filter(pk=wh_id).first() if wh_id else None
        sh = Shift.objects.filter(pk=shift_id).first() if shift_id else None
        usr = User.objects.filter(pk=user_id).first() if user_id else None

        emp = Employee.objects.create(
            employee_code=EmployeeService.generate_employee_code(),
            full_name=full_name,
            phone=phone,
            email=email,
            date_of_birth=dob,
            joining_date=joining_date,
            department=dept,
            designation=desig,
            primary_warehouse=wh,
            shift=sh,
            user=usr,
            address=address,
            emergency_contact=emergency,
            notes=notes,
            status='active'
        )

        messages.success(request, f"Employee '{emp.full_name}' ({emp.employee_code}) enrolled successfully.")
        return redirect('employee-list')

class EmployeeDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        emp = get_object_or_404(Employee, pk=pk)
        recent_atts = Attendance.objects.filter(employee=emp)[:30]
        recent_leaves = LeaveRequest.objects.filter(employee=emp)[:10]

        context = {
            'employee': emp,
            'attendances': recent_atts,
            'leaves': recent_leaves,
            'active_menu': 'employees'
        }
        return render(request, 'employees/employee_detail.html', context)

class AttendanceDashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        EmployeeService.seed_default_org_data()
        today = timezone.now().date()
        today_atts = Attendance.objects.select_related('employee', 'warehouse').filter(date=today)
        summary = EmployeeService.get_attendance_summary_today()
        employees = Employee.objects.filter(status='active')

        context = {
            'summary': summary,
            'attendances': today_atts,
            'employees': employees,
            'warehouses': Warehouse.objects.filter(status='active'),
            'today': today,
            'active_menu': 'employees'
        }
        return render(request, 'employees/attendance_dashboard.html', context)

class AttendanceCheckInView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        employee_id = request.POST.get('employee')
        wh_id = request.POST.get('warehouse')

        emp = get_object_or_404(Employee, pk=employee_id)
        wh = Warehouse.objects.filter(pk=wh_id).first() if wh_id else None

        try:
            att = EmployeeService.record_check_in(emp, warehouse=wh, source='web', user=request.user)
            messages.success(request, f"Check-In recorded for '{emp.full_name}' at {att.check_in.strftime('%H:%M')}.")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('attendance-dashboard')

class AttendanceCheckOutView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        employee_id = request.POST.get('employee')
        emp = get_object_or_404(Employee, pk=employee_id)

        try:
            att = EmployeeService.record_check_out(emp)
            messages.success(request, f"Check-Out recorded for '{emp.full_name}' ({att.working_hours} working hrs).")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('attendance-dashboard')

class AttendanceCalendarView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        today = timezone.now().date()
        emp_id = request.GET.get('employee')
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))

        employees = Employee.objects.filter(status='active')
        sel_emp = Employee.objects.filter(pk=emp_id).first() if emp_id else employees.first()

        atts = []
        if sel_emp:
            atts = Attendance.objects.filter(employee=sel_emp, date__year=year, date__month=month)

        context = {
            'employees': employees,
            'selected_employee': sel_emp,
            'attendances': atts,
            'month': month,
            'year': year,
            'active_menu': 'employees'
        }
        return render(request, 'employees/attendance_calendar.html', context)

class LeaveListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        leaves = LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by').all()
        context = {
            'leaves': leaves,
            'active_menu': 'employees'
        }
        return render(request, 'employees/leave_list.html', context)

class LeaveCreateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        EmployeeService.seed_default_org_data()
        employees = Employee.objects.filter(status='active')
        leave_types = LeaveType.objects.all()

        context = {
            'employees': employees,
            'leave_types': leave_types,
            'active_menu': 'employees'
        }
        return render(request, 'employees/leave_create.html', context)

    def post(self, request):
        employee_id = request.POST.get('employee')
        type_id = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        num_days = request.POST.get('number_of_days', 1.0)
        reason = request.POST.get('reason', '')

        emp = get_object_or_404(Employee, pk=employee_id)
        lt = get_object_or_404(LeaveType, pk=type_id)

        lr = LeaveRequest.objects.create(
            employee=emp,
            leave_type=lt,
            start_date=start_date,
            end_date=end_date,
            number_of_days=Decimal(str(num_days)),
            reason=reason,
            status='pending'
        )

        messages.success(request, f"Leave application submitted for '{emp.full_name}'.")
        return redirect('leave-list')

class LeaveApproveView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        lr = get_object_or_404(LeaveRequest, pk=pk)
        EmployeeService.approve_leave(lr, request.user)
        messages.success(request, f"Leave request for '{lr.employee.full_name}' approved.")
        return redirect('leave-list')
