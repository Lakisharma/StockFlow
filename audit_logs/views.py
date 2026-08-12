from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from users.services import RBACService
from users.models import User
from .models import SystemAuditLog
from .services import AuditLogService

class AuditLogListView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'reports', 'view'):
            messages.error(request, "You do not have authorization to access System Audit Logs.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        metrics = AuditLogService.get_audit_metrics()
        logs_qs = SystemAuditLog.objects.select_related('user').all()

        search = request.GET.get('search')
        module_filter = request.GET.get('module')
        action_filter = request.GET.get('action')
        status_filter = request.GET.get('status')
        user_filter = request.GET.get('user')
        date_range = request.GET.get('date_range', 'all')

        # Date range filtering
        now = timezone.now()
        if date_range == 'today':
            logs_qs = logs_qs.filter(timestamp__date=now.date())
        elif date_range == 'yesterday':
            logs_qs = logs_qs.filter(timestamp__date=now.date() - timedelta(days=1))
        elif date_range == 'this_week':
            start_week = now - timedelta(days=now.weekday())
            logs_qs = logs_qs.filter(timestamp__gte=start_week)
        elif date_range == 'this_month':
            logs_qs = logs_qs.filter(timestamp__year=now.year, timestamp__month=now.month)
        elif date_range == 'last_month':
            first_this_month = now.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            logs_qs = logs_qs.filter(timestamp__year=last_month_end.year, timestamp__month=last_month_end.month)

        if search:
            logs_qs = logs_qs.filter(
                models.Q(description__icontains=search) |
                models.Q(log_id__icontains=search) |
                models.Q(record_id__icontains=search) |
                models.Q(user__username__icontains=search)
            )

        if module_filter:
            logs_qs = logs_qs.filter(module=module_filter)
        if action_filter:
            logs_qs = logs_qs.filter(action__icontains=action_filter)
        if status_filter:
            logs_qs = logs_qs.filter(status=status_filter)
        if user_filter:
            logs_qs = logs_qs.filter(user_id=user_filter)

        paginator = Paginator(logs_qs, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'metrics': metrics,
            'page_obj': page_obj,
            'users': User.objects.filter(is_active=True),
            'search': search,
            'module_filter': module_filter,
            'action_filter': action_filter,
            'status_filter': status_filter,
            'user_filter': user_filter,
            'date_range': date_range,
            'active_menu': 'audit'
        }
        return render(request, 'audit_logs/audit_log_list.html', context)

class AuditLogTimelineView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        logs = SystemAuditLog.objects.select_related('user').all()[:100]
        return render(request, 'audit_logs/audit_log_timeline.html', {'logs': logs, 'active_menu': 'audit'})

class AuditLogDetailView(View):
    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')
        log = get_object_or_404(SystemAuditLog, pk=pk)
        return render(request, 'audit_logs/audit_log_detail.html', {'log': log, 'active_menu': 'audit'})

class AuditLogExportView(View):
    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, "Permission denied to export audit logs.")
            return redirect('audit-log-list')

        logs_qs = SystemAuditLog.objects.select_related('user').all()
        csv_data = AuditLogService.generate_csv(logs_qs)

        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="StockFlow_Audit_Logs_{timezone.now().strftime("%Y%m%d")}.csv"'
        return response
