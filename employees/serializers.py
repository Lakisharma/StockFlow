from rest_framework import serializers
from .models import Department, Designation, Shift, Employee, Attendance, LeaveType, LeaveRequest, Holiday

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'status', 'created_at']

class DesignationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Designation
        fields = ['id', 'name', 'department', 'department_name', 'description', 'created_at']

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['id', 'name', 'start_time', 'end_time', 'grace_period_mins', 'break_duration_mins', 'status', 'created_at']

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    warehouse_name = serializers.CharField(source='primary_warehouse.name', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'full_name', 'profile_photo', 'phone', 'email',
            'date_of_birth', 'joining_date', 'department', 'department_name',
            'designation', 'designation_name', 'primary_warehouse', 'warehouse_name',
            'shift', 'shift_name', 'address', 'emergency_contact', 'status', 'user', 'notes', 'created_at'
        ]

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_code', 'date', 'check_in', 'check_out',
            'working_hours', 'late_minutes', 'early_leaving_minutes', 'overtime_hours',
            'status', 'warehouse', 'remarks', 'source', 'created_by', 'created_at'
        ]

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'number_of_days', 'reason', 'status',
            'applied_date', 'approved_by', 'rejection_reason'
        ]

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'name', 'date', 'holiday_type', 'description']
