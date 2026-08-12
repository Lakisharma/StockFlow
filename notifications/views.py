from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Notification, NotificationPreference
from .services import NotificationService

class NotificationCenterView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # Auto-trigger stock alert scan when loading notification center
        NotificationService.dispatch_stock_alerts()

        qs = Notification.objects.filter(user=request.user)

        search = request.GET.get('search')
        status_filter = request.GET.get('status', 'all')
        priority_filter = request.GET.get('priority')
        module_filter = request.GET.get('module')

        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(message__icontains=search)
        if status_filter == 'unread':
            qs = qs.filter(is_read=False)
        elif status_filter == 'read':
            qs = qs.filter(is_read=True)

        if priority_filter:
            qs = qs.filter(priority=priority_filter)
        if module_filter:
            qs = qs.filter(module=module_filter)

        paginator = Paginator(qs, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        summary = NotificationService.get_user_notifications(request.user)

        context = {
            'page_obj': page_obj,
            'summary': summary,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'module_filter': module_filter,
            'search': search,
            'active_menu': 'notifications'
        }
        return render(request, 'notifications/notification_center.html', context)

class NotificationMarkReadView(View):
    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return redirect('login')

        if pk:
            NotificationService.mark_as_read(pk, request.user)
            messages.success(request, "Notification marked as read.")
        else:
            NotificationService.mark_all_read(request.user)
            messages.success(request, "All notifications marked as read.")

        next_url = request.META.get('HTTP_REFERER', '/notifications/')
        return redirect(next_url)

class NotificationDeleteView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.delete()
        messages.success(request, "Notification removed.")
        return redirect('notification-center')

class NotificationPreferencesView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        pref = NotificationService.get_user_preferences(request.user)
        return render(request, 'notifications/preferences.html', {'pref': pref, 'active_menu': 'notifications'})

    def post(self, request):
        pref = NotificationService.get_user_preferences(request.user)
        pref.notify_low_stock = request.POST.get('notify_low_stock') == 'on'
        pref.notify_out_of_stock = request.POST.get('notify_out_of_stock') == 'on'
        pref.notify_purchases = request.POST.get('notify_purchases') == 'on'
        pref.notify_transfers = request.POST.get('notify_transfers') == 'on'
        pref.notify_ocr = request.POST.get('notify_ocr') == 'on'
        pref.notify_backups = request.POST.get('notify_backups') == 'on'
        pref.notify_security = request.POST.get('notify_security') == 'on'
        pref.save()

        messages.success(request, "Notification preferences saved successfully.")
        return redirect('notification-preferences')
