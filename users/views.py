from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from products.models import Warehouse
from .models import Role, RolePermission, UserProfile, UserActivityLog
from .services import RBACService, ALL_MODULES

class UserListView(View):
    def get(self, request):
        RBACService.seed_default_roles()
        # Make sure profiles exist
        for u in User.objects.all():
            RBACService.ensure_user_profile(u)

        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        role_filter = request.GET.get('role', '')

        users = User.objects.select_related('profile', 'profile__role').prefetch_related('profile__assigned_warehouses').filter(profile__is_soft_deleted=False)

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(profile__phone__icontains=search)
            )

        if status_filter:
            users = users.filter(profile__status=status_filter)

        if role_filter:
            users = users.filter(profile__role_id=role_filter)

        roles = Role.objects.all()

        return render(request, 'users/user_list.html', {
            'users': users,
            'roles': roles,
            'search': search,
            'selected_status': status_filter,
            'selected_role': role_filter
        })

class UserCreateView(View):
    def get(self, request):
        RBACService.seed_default_roles()
        roles = Role.objects.all()
        warehouses = Warehouse.objects.filter(status='active')
        return render(request, 'users/user_form.html', {
            'roles': roles,
            'warehouses': warehouses
        })

    def post(self, request):
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role_id = request.POST.get('role')
        status = request.POST.get('status', 'active')
        access_type = request.POST.get('warehouse_access_type', 'all')
        assigned_wh_ids = request.POST.getlist('assigned_warehouses')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('user-add')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect('user-add')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists!")
            return redirect('user-add')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        role = Role.objects.filter(id=role_id).first() if role_id else Role.objects.filter(name='Viewer').first()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = phone
        profile.status = status
        profile.warehouse_access_type = access_type
        profile.save()

        if access_type == 'selected' and assigned_wh_ids:
            profile.assigned_warehouses.set(assigned_wh_ids)

        RBACService.log_activity(request.user, f"Created User account '{username}' ({role.name if role else 'No Role'})", "Users", reference=str(user.id), request=request)
        messages.success(request, f"User '{username}' created successfully!")
        return redirect('user-list')

class UserUpdateView(View):
    def get(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        profile = RBACService.ensure_user_profile(user_obj)
        roles = Role.objects.all()
        warehouses = Warehouse.objects.filter(status='active')

        return render(request, 'users/user_form.html', {
            'user_obj': user_obj,
            'profile': profile,
            'roles': roles,
            'warehouses': warehouses
        })

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        profile = RBACService.ensure_user_profile(user_obj)

        user_obj.first_name = request.POST.get('first_name', user_obj.first_name)
        user_obj.last_name = request.POST.get('last_name', user_obj.last_name)
        user_obj.email = request.POST.get('email', user_obj.email)
        user_obj.save()

        role_id = request.POST.get('role')
        if role_id:
            profile.role = Role.objects.filter(id=role_id).first()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.status = request.POST.get('status', profile.status)
        profile.warehouse_access_type = request.POST.get('warehouse_access_type', profile.warehouse_access_type)
        profile.save()

        if profile.warehouse_access_type == 'selected':
            assigned_wh_ids = request.POST.getlist('assigned_warehouses')
            profile.assigned_warehouses.set(assigned_wh_ids)
        else:
            profile.assigned_warehouses.clear()

        RBACService.log_activity(request.user, f"Updated User profile for '{user_obj.username}'", "Users", reference=str(user_obj.id), request=request)
        messages.success(request, f"User '{user_obj.username}' updated successfully!")
        return redirect('user-list')

class UserDetailView(View):
    def get(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        profile = RBACService.ensure_user_profile(user_obj)
        permissions = RolePermission.objects.filter(role=profile.role) if profile.role else []
        activity_logs = UserActivityLog.objects.filter(user=user_obj)[:20]

        return render(request, 'users/user_detail.html', {
            'user_obj': user_obj,
            'profile': profile,
            'permissions': permissions,
            'activity_logs': activity_logs
        })

class UserDeactivateView(View):
    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        profile = RBACService.ensure_user_profile(user_obj)

        if profile.status == 'active':
            profile.status = 'inactive'
            user_obj.is_active = False
            msg = f"User '{user_obj.username}' has been deactivated."
        else:
            profile.status = 'active'
            user_obj.is_active = True
            msg = f"User '{user_obj.username}' has been reactivated."

        user_obj.save()
        profile.save()

        RBACService.log_activity(request.user, f"Toggled User status for '{user_obj.username}' to {profile.status}", "Users", reference=str(user_obj.id), request=request)
        messages.success(request, msg)
        return redirect('user-list')

class UserSoftDeleteView(View):
    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        profile = RBACService.ensure_user_profile(user_obj)

        profile.is_soft_deleted = True
        profile.status = 'inactive'
        profile.save()

        user_obj.is_active = False
        user_obj.save()

        RBACService.log_activity(request.user, f"Soft-deleted User account '{user_obj.username}'", "Users", reference=str(user_obj.id), request=request)
        messages.success(request, f"User '{user_obj.username}' has been archived/deleted.")
        return redirect('user-list')

class UserResetPasswordView(View):
    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect('user-detail', pk=user_obj.id)

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect('user-detail', pk=user_obj.id)

        user_obj.set_password(new_password)
        user_obj.save()

        RBACService.log_activity(request.user, f"Reset password for User '{user_obj.username}'", "Users", reference=str(user_obj.id), request=request)
        messages.success(request, f"Password for '{user_obj.username}' has been reset successfully!")
        return redirect('user-detail', pk=user_obj.id)

class SelfProfileView(View):
    def get(self, request):
        profile = RBACService.ensure_user_profile(request.user)
        return render(request, 'users/self_profile.html', {'profile': profile})

    def post(self, request):
        user = request.user
        profile = RBACService.ensure_user_profile(user)

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.save()

        # Change password if provided
        old_pw = request.POST.get('old_password')
        new_pw = request.POST.get('new_password')
        confirm_pw = request.POST.get('confirm_password')

        if new_pw:
            if not user.check_password(old_pw):
                messages.error(request, "Current password is incorrect!")
                return redirect('self-profile')
            if new_pw != confirm_pw:
                messages.error(request, "New passwords do not match!")
                return redirect('self-profile')
            user.set_password(new_pw)
            user.save()

        RBACService.log_activity(user, "Updated own profile details", "Users", request=request)
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('self-profile')

class RoleListView(View):
    def get(self, request):
        RBACService.seed_default_roles()
        roles = Role.objects.prefetch_related('permissions').all()
        return render(request, 'users/role_list.html', {'roles': roles})

class RoleCreateView(View):
    def get(self, request):
        return render(request, 'users/role_form.html', {
            'modules': RolePermission.MODULE_CHOICES
        })

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')

        if Role.objects.filter(name=name).exists():
            messages.error(request, f"Role '{name}' already exists!")
            return redirect('role-add')

        role = Role.objects.create(name=name, description=description, is_system_role=False)

        for mod_key, mod_label in RolePermission.MODULE_CHOICES:
            can_v = request.POST.get(f'perm_{mod_key}_view') == 'on'
            can_c = request.POST.get(f'perm_{mod_key}_create') == 'on'
            can_e = request.POST.get(f'perm_{mod_key}_edit') == 'on'
            can_d = request.POST.get(f'perm_{mod_key}_delete') == 'on'
            can_x = request.POST.get(f'perm_{mod_key}_export') == 'on'
            can_a = request.POST.get(f'perm_{mod_key}_approve') == 'on'
            can_p = request.POST.get(f'perm_{mod_key}_print') == 'on'

            RolePermission.objects.create(
                role=role, module=mod_key,
                can_view=can_v, can_create=can_c, can_edit=can_e,
                can_delete=can_d, can_export=can_x, can_approve=can_a, can_print=can_p
            )

        RBACService.log_activity(request.user, f"Created custom Role '{name}'", "Roles", reference=str(role.id), request=request)
        messages.success(request, f"Custom Role '{name}' created successfully!")
        return redirect('role-list')

class RoleUpdateView(View):
    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        permissions_dict = {p.module: p for p in role.permissions.all()}

        return render(request, 'users/role_form.html', {
            'role': role,
            'modules': RolePermission.MODULE_CHOICES,
            'permissions_dict': permissions_dict
        })

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        role.description = request.POST.get('description', role.description)
        role.save()

        for mod_key, mod_label in RolePermission.MODULE_CHOICES:
            perm, _ = RolePermission.objects.get_or_create(role=role, module=mod_key)
            perm.can_view = request.POST.get(f'perm_{mod_key}_view') == 'on'
            perm.can_create = request.POST.get(f'perm_{mod_key}_create') == 'on'
            perm.can_edit = request.POST.get(f'perm_{mod_key}_edit') == 'on'
            perm.can_delete = request.POST.get(f'perm_{mod_key}_delete') == 'on'
            perm.can_export = request.POST.get(f'perm_{mod_key}_export') == 'on'
            perm.can_approve = request.POST.get(f'perm_{mod_key}_approve') == 'on'
            perm.can_print = request.POST.get(f'perm_{mod_key}_print') == 'on'
            perm.save()

        RBACService.log_activity(request.user, f"Updated permissions for Role '{role.name}'", "Roles", reference=str(role.id), request=request)
        messages.success(request, f"Role permissions for '{role.name}' updated successfully!")
        return redirect('role-list')

class RoleDeleteView(View):
    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        if role.is_system_role:
            messages.error(request, f"System role '{role.name}' cannot be deleted.")
            return redirect('role-list')

        name = role.name
        role.delete()
        RBACService.log_activity(request.user, f"Deleted custom Role '{name}'", "Roles", request=request)
        messages.success(request, f"Custom role '{name}' deleted successfully.")
        return redirect('role-list')

class UserActivityLogView(View):
    def get(self, request):
        logs = UserActivityLog.objects.select_related('user').all()[:100]
        return render(request, 'users/activity_logs.html', {'logs': logs})
