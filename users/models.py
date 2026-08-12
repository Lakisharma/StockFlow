from django.db import models
from django.contrib.auth.models import User
from products.models import Warehouse

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_system_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class RolePermission(models.Model):
    MODULE_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('categories', 'Categories'),
        ('units', 'Units'),
        ('brands', 'Brands'),
        ('products', 'Products'),
        ('suppliers', 'Suppliers'),
        ('warehouses', 'Warehouses'),
        ('purchases', 'Purchases'),
        ('inventory', 'Inventory'),
        ('transfers', 'Stock Transfers'),
        ('ocr', 'OCR Scanner'),
        ('reports', 'Reports'),
        ('users', 'Users'),
        ('roles', 'Roles'),
        ('settings', 'Settings'),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module = models.CharField(max_length=30, choices=MODULE_CHOICES)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'module')

    def __str__(self):
        return f"{self.role.name} - {self.get_module_display()}"

class UserProfile(models.Model):
    WAREHOUSE_ACCESS_CHOICES = [
        ('all', 'All Warehouses'),
        ('selected', 'Selected Warehouses'),
        ('none', 'No Warehouse'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    warehouse_access_type = models.CharField(max_length=20, choices=WAREHOUSE_ACCESS_CHOICES, default='all')
    assigned_warehouses = models.ManyToManyField(Warehouse, blank=True, related_name='assigned_users')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_soft_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role.name if self.role else 'No Role'})"

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user.username if self.user else 'System'}: {self.action}"
