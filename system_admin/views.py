from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from users.models import UserProfile
from audit_logs.models import SystemAuditLog
from .models import DocumentSequence, SecurityPolicy, UserFailedLogin
from .services import SystemAdminService, SystemHealthService

class AdminControlCenterView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, "Access Restricted to System Administrators.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        metrics = SystemAdminService.get_security_metrics()
        health = SystemHealthService.run_health_check()
        recent_logs = SystemAuditLog.objects.all()[:15]

        context = {
            'metrics': metrics,
            'health': health,
            'recent_logs': recent_logs,
            'active_menu': 'admin_center'
        }
        return render(request, 'system_admin/control_center.html', context)

class SecurityDashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        policy = SystemAdminService.get_security_policy()
        failed_attempts = UserFailedLogin.objects.filter(is_resolved=False)[:20]
        locked_profiles = UserProfile.objects.select_related('user').filter(status='inactive')

        context = {
            'policy': policy,
            'failed_attempts': failed_attempts,
            'locked_profiles': locked_profiles,
            'active_menu': 'admin_center'
        }
        return render(request, 'system_admin/security_dashboard.html', context)

    def post(self, request):
        policy = SystemAdminService.get_security_policy()
        policy.max_failed_attempts = int(request.POST.get('max_failed_attempts', 5))
        policy.lockout_duration_mins = int(request.POST.get('lockout_duration_mins', 30))
        policy.min_password_length = int(request.POST.get('min_password_length', 8))
        policy.inactivity_timeout_mins = int(request.POST.get('inactivity_timeout_mins', 30))
        policy.enable_maintenance_mode = 'enable_maintenance_mode' in request.POST
        policy.maintenance_message = request.POST.get('maintenance_message', policy.maintenance_message)
        policy.save()

        messages.success(request, "Security Policy and Maintenance Mode settings updated successfully.")
        return redirect('admin-security')

class DocumentNumberingView(View):
    def get(self, request):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return redirect('dashboard')

        sequences = DocumentSequence.objects.all()
        return render(request, 'system_admin/document_numbering.html', {'sequences': sequences, 'active_menu': 'admin_center'})

    def post(self, request):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return redirect('dashboard')

        seq_id = request.POST.get('sequence_id')
        prefix = request.POST.get('prefix')
        next_num = int(request.POST.get('next_number', 1))

        seq = get_object_or_404(DocumentSequence, pk=seq_id)
        seq.prefix = prefix
        seq.next_number = next_num
        seq.save()

        messages.success(request, f"Document Sequence for '{seq.get_document_type_display()}' updated to prefix '{prefix}' (Next: {next_num}).")
        return redirect('admin-numbering')

class SystemHealthView(View):
    def get(self, request):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return redirect('dashboard')

        health = SystemHealthService.run_health_check()
        return render(request, 'system_admin/system_health.html', {'health': health, 'active_menu': 'admin_center'})

class UserLockoutManagementView(View):
    def post(self, request, user_id):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return redirect('dashboard')

        user = get_object_or_404(User, pk=user_id)
        SystemAdminService.unlock_user_account(user)

        messages.success(request, f"User account '{user.username}' has been unlocked successfully.")
        return redirect('admin-security')
