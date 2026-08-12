from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('departments', api_views.DepartmentViewSet, basename='api-department')
router.register('designations', api_views.DesignationViewSet, basename='api-designation')
router.register('shifts', api_views.ShiftViewSet, basename='api-shift')
router.register('list', api_views.EmployeeViewSet, basename='api-employee')
router.register('attendance', api_views.AttendanceViewSet, basename='api-attendance')
router.register('leaves', api_views.LeaveRequestViewSet, basename='api-leave')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Employee Directory & Profile
    path('', views.EmployeeListView.as_view(), name='employee-list'),
    path('create/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),

    # Attendance
    path('attendance/', views.AttendanceDashboardView.as_view(), name='attendance-dashboard'),
    path('attendance/list/', views.AttendanceDashboardView.as_view(), name='attendance-list'),
    path('attendance/check-in/', views.AttendanceCheckInView.as_view(), name='attendance-check-in'),
    path('attendance/check-out/', views.AttendanceCheckOutView.as_view(), name='attendance-check-out'),
    path('attendance/calendar/', views.AttendanceCalendarView.as_view(), name='attendance-calendar'),

    # Leave Management
    path('leaves/', views.LeaveListView.as_view(), name='leave-list'),
    path('leaves/create/', views.LeaveCreateView.as_view(), name='leave-create'),
    path('leaves/<int:pk>/approve/', views.LeaveApproveView.as_view(), name='leave-approve'),
]
