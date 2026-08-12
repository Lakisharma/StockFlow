from django.shortcuts import render
from .models import SecurityPolicy

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        policy = SecurityPolicy.objects.filter(id=1).first()
        if policy and policy.enable_maintenance_mode:
            # Exempt superusers, staff, login endpoints, static files, and admin-center
            user = request.user
            is_exempt_user = user and user.is_authenticated and (user.is_superuser or user.is_staff)
            path = request.path_info.lower()
            is_exempt_path = path.startswith('/login') or path.startswith('/admin') or path.startswith('/static') or path.startswith('/media')

            if not is_exempt_user and not is_exempt_path:
                return render(request, 'system_admin/maintenance_notice.html', {'message': policy.maintenance_message}, status=503)

        response = self.get_response(request)
        return response
