from django.db import models
from django.contrib.auth.models import User
from products.models import Warehouse

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Designation(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='designations')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.department.name if self.department else 'General'})"

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_mins = models.IntegerField(default=15)
    break_duration_mins = models.IntegerField(default=60)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class Employee(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
    )

    employee_code = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    profile_photo = models.ImageField(upload_to='employees/photos/', null=True, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joining_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    primary_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('late', 'Late'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday'),
        ('weekly_off', 'Weekly Off'),
        ('wfh', 'Work From Home'),
    )

    SOURCE_CHOICES = (
        ('web', 'Web Portal'),
        ('mobile', 'Mobile App'),
        ('manual', 'Manual Entry'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(db_index=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_minutes = models.IntegerField(default=0)
    early_leaving_minutes = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.status})"

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True)
    default_days_per_year = models.IntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

class Holiday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(unique=True)
    holiday_type = models.CharField(max_length=50, default='national')
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"
