import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import FileResponse, Http404
from users.services import RBACService
from .models import BackupRecord, BackupSettings
from .services import BackupEngineService

class BackupDashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'view'):
            messages.error(request, "You do not have administrative authorization to access Backup & Restore.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        metrics = BackupEngineService.get_storage_metrics()
        backups_qs = BackupRecord.objects.all()

        search = request.GET.get('search')
        type_filter = request.GET.get('type')
        status_filter = request.GET.get('status')

        if search:
            backups_qs = backups_qs.filter(backup_name__icontains=search) | backups_qs.filter(backup_id__icontains=search)
        if type_filter:
            backups_qs = backups_qs.filter(backup_type=type_filter)
        if status_filter:
            backups_qs = backups_qs.filter(status=status_filter)

        context = {
            'metrics': metrics,
            'backups': backups_qs[:50],
            'type_filter': type_filter,
            'status_filter': status_filter,
            'search': search,
            'active_menu': 'backups'
        }
        return render(request, 'backups/backup_dashboard.html', context)

class BackupCreateView(View):
    def post(self, request):
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'create'):
            messages.error(request, "Permission denied to create backups.")
            return redirect('backup-dashboard')

        custom_name = request.POST.get('backup_name')
        try:
            record = BackupEngineService.create_backup(user=request.user, backup_type='manual', custom_name=custom_name)
            messages.success(request, f"Backup '{record.backup_id}' created and verified successfully ({record.file_size_mb} MB).")
        except Exception as e:
            messages.error(request, f"Backup creation failed: {str(e)}")

        return redirect('backup-dashboard')

class BackupDetailView(View):
    def get(self, request, pk):
        record = get_object_or_404(BackupRecord, pk=pk)
        return render(request, 'backups/backup_detail.html', {'backup': record, 'active_menu': 'backups'})

class BackupDownloadView(View):
    def get(self, request, pk):
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'export'):
            messages.error(request, "Permission denied to download backup files.")
            return redirect('backup-dashboard')

        record = get_object_or_404(BackupRecord, pk=pk)
        if not record.file_path or not os.path.exists(record.file_path):
            raise Http404("Backup file not found on server.")

        RBACService.log_activity(request.user, f"Downloaded Backup File '{record.backup_id}'", "Backup & Restore", reference=record.backup_id, request=request)
        response = FileResponse(open(record.file_path, 'rb'), as_attachment=True, filename=f"{record.backup_id}.zip")
        return response

class BackupRestoreView(View):
    def post(self, request, pk):
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'edit'):
            messages.error(request, "Permission denied to perform system restoration.")
            return redirect('backup-dashboard')

        record = get_object_or_404(BackupRecord, pk=pk)
        try:
            BackupEngineService.restore_backup(record, user=request.user)
            messages.success(request, f"System restored successfully from Backup '{record.backup_id}'. Pre-restore safety backup was automatically created.")
        except Exception as e:
            messages.error(request, f"System restoration failed: {str(e)}")

        return redirect('backup-dashboard')

class BackupDeleteView(View):
    def post(self, request, pk):
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'delete'):
            messages.error(request, "Permission denied to delete backups.")
            return redirect('backup-dashboard')

        record = get_object_or_404(BackupRecord, pk=pk)
        b_id = record.backup_id
        if record.file_path and os.path.exists(record.file_path):
            try:
                os.remove(record.file_path)
            except OSError:
                pass
        record.delete()
        RBACService.log_activity(request.user, f"Deleted Backup '{b_id}'", "Backup & Restore", reference=b_id, request=request)
        messages.success(request, f"Backup '{b_id}' deleted successfully.")
        return redirect('backup-dashboard')

class BackupSettingsView(View):
    def post(self, request):
        if not request.user.is_superuser and not RBACService.has_permission(request.user, 'settings', 'edit'):
            messages.error(request, "Permission denied to modify backup settings.")
            return redirect('backup-dashboard')

        b_settings = BackupEngineService.get_backup_settings()
        b_settings.auto_backup_enabled = request.POST.get('auto_backup_enabled') == 'on'
        b_settings.frequency = request.POST.get('frequency', b_settings.frequency)
        b_settings.backup_time = request.POST.get('backup_time', b_settings.backup_time)
        b_settings.retention_policy = request.POST.get('retention_policy', b_settings.retention_policy)
        b_settings.save()

        RBACService.log_activity(request.user, "Updated Automatic Backup & Retention Settings", "Backup & Restore", request=request)
        messages.success(request, "Automatic Backup & Retention preferences saved successfully.")
        return redirect('backup-dashboard')
