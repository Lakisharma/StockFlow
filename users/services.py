from django.contrib.auth.models import User
from products.models import Warehouse
from .models import Role, RolePermission, UserProfile, UserActivityLog

DEFAULT_ROLES = [
    ('Super Admin', 'Full unrestricted enterprise system administration access', True),
    ('Admin', 'Administrative management access to all modules', True),
    ('Manager', 'Operations manager overseeing stock, purchases, and godowns', True),
    ('Warehouse Staff', 'Godown staff handling physical stock movement and transfers', True),
    ('Purchase Staff', 'Procurement staff managing purchase orders and suppliers', True),
    ('Inventory Staff', 'Stock handlers managing product catalogs and inventory levels', True),
    ('Accountant', 'Financial accountant handling purchases, GST tax, and valuation', True),
    ('Viewer', 'Read-only audit access across all modules', True),
]

ALL_MODULES = [
    'dashboard', 'categories', 'units', 'brands', 'products', 'suppliers',
    'warehouses', 'purchases', 'inventory', 'transfers', 'ocr', 'reports',
    'users', 'roles', 'settings'
]

class RBACService:

    @classmethod
    def seed_default_roles(cls):
        created_roles = {}
        for name, desc, is_sys in DEFAULT_ROLES:
            role, _ = Role.objects.get_or_create(name=name, defaults={'description': desc, 'is_system_role': is_sys})
            created_roles[name] = role

            # Create default matrix permissions for each module
            for mod in ALL_MODULES:
                perm, _ = RolePermission.objects.get_or_create(role=role, module=mod)

                if name == 'Super Admin':
                    perm.can_view = True; perm.can_create = True; perm.can_edit = True
                    perm.can_delete = True; perm.can_export = True; perm.can_approve = True; perm.can_print = True
                elif name == 'Admin':
                    perm.can_view = True; perm.can_create = True; perm.can_edit = True
                    perm.can_delete = (mod != 'settings'); perm.can_export = True; perm.can_approve = True; perm.can_print = True
                elif name == 'Manager':
                    perm.can_view = True; perm.can_create = True; perm.can_edit = True
                    perm.can_delete = False; perm.can_export = True; perm.can_approve = True; perm.can_print = True
                elif name == 'Warehouse Staff':
                    is_target = mod in ['dashboard', 'products', 'warehouses', 'inventory', 'transfers', 'ocr']
                    perm.can_view = is_target; perm.can_create = is_target; perm.can_edit = is_target
                    perm.can_delete = False; perm.can_export = is_target; perm.can_approve = False; perm.can_print = is_target
                elif name == 'Purchase Staff':
                    is_target = mod in ['dashboard', 'products', 'suppliers', 'purchases', 'ocr', 'reports']
                    perm.can_view = is_target; perm.can_create = is_target; perm.can_edit = is_target
                    perm.can_delete = False; perm.can_export = is_target; perm.can_approve = (mod == 'purchases'); perm.can_print = is_target
                elif name == 'Inventory Staff':
                    is_target = mod in ['dashboard', 'categories', 'units', 'brands', 'products', 'inventory', 'transfers']
                    perm.can_view = is_target; perm.can_create = is_target; perm.can_edit = is_target
                    perm.can_delete = False; perm.can_export = is_target; perm.can_approve = False; perm.can_print = is_target
                elif name == 'Accountant':
                    is_target = mod in ['dashboard', 'suppliers', 'purchases', 'reports']
                    perm.can_view = is_target; perm.can_create = False; perm.can_edit = False
                    perm.can_delete = False; perm.can_export = is_target; perm.can_approve = False; perm.can_print = is_target
                elif name == 'Viewer':
                    perm.can_view = True; perm.can_create = False; perm.can_edit = False
                    perm.can_delete = False; perm.can_export = True; perm.can_approve = False; perm.can_print = True

                perm.save()

        return created_roles

    @classmethod
    def ensure_user_profile(cls, user, role_name='Viewer'):
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.role:
            cls.seed_default_roles()
            profile.role = Role.objects.filter(name='Super Admin' if user.is_superuser else role_name).first()
            profile.save()
        return profile

    @classmethod
    def has_permission(cls, user, module, action='view'):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        profile = getattr(user, 'profile', None)
        if not profile or not profile.role or profile.status != 'active' or profile.is_soft_deleted:
            return False

        perm = RolePermission.objects.filter(role=profile.role, module=module).first()
        if not perm:
            return False

        action_attr_map = {
            'view': 'can_view',
            'create': 'can_create',
            'edit': 'can_edit',
            'delete': 'can_delete',
            'export': 'can_export',
            'approve': 'can_approve',
            'print': 'can_print',
        }
        attr = action_attr_map.get(action.lower(), 'can_view')
        return getattr(perm, attr, False)

    @classmethod
    def get_user_warehouses(cls, user):
        if not user.is_authenticated or user.is_superuser:
            return Warehouse.objects.all()

        profile = getattr(user, 'profile', None)
        if not profile or profile.warehouse_access_type == 'all':
            return Warehouse.objects.all()
        elif profile.warehouse_access_type == 'selected':
            return profile.assigned_warehouses.all()
        else:
            return Warehouse.objects.none()

    @classmethod
    def log_activity(cls, user, action, module, reference=None, request=None):
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

        UserActivityLog.objects.create(
            user=user if user.is_authenticated else None,
            action=action,
            module=module,
            reference=reference,
            ip_address=ip
        )
