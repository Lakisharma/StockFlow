from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Department, Designation, Shift, Employee, Attendance, LeaveType, LeaveRequest, Holiday
from .serializers import (
    DepartmentSerializer, DesignationSerializer, ShiftSerializer,
    EmployeeSerializer, AttendanceSerializer, LeaveRequestSerializer, HolidaySerializer
)
from .services import EmployeeService

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class DesignationViewSet(viewsets.ModelViewSet):
    queryset = Designation.objects.select_related('department').all()
    serializer_class = DesignationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name']

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('department', 'designation', 'primary_warehouse', 'shift', 'user').all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['employee_code', 'full_name', 'phone', 'email', 'department__name', 'designation__name']
    ordering_fields = ['joining_date', 'full_name', 'created_at']

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('employee', 'warehouse', 'created_by').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['employee__full_name', 'employee__employee_code', 'date', 'status']
    ordering_fields = ['date', 'check_in', 'created_at']

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        employee_id = request.data.get('employee_id')
        emp = Employee.objects.filter(pk=employee_id).first()
        if not emp:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            att = EmployeeService.record_check_in(emp, source='mobile', user=request.user)
            return Response(AttendanceSerializer(att).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        employee_id = request.data.get('employee_id')
        emp = Employee.objects.filter(pk=employee_id).first()
        if not emp:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            att = EmployeeService.record_check_out(emp)
            return Response(AttendanceSerializer(att).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by').all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['employee__full_name', 'leave_type__name', 'status']
    ordering_fields = ['applied_date', 'start_date']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_req = self.get_object()
        EmployeeService.approve_leave(leave_req, request.user)
        return Response(LeaveRequestSerializer(leave_req).data, status=status.HTTP_200_OK)
