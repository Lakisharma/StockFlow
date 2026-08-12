from django.utils import timezone
from django.contrib.auth.models import User
from products.models import WarehouseStock
from users.services import RBACService
from .models import Notification, NotificationPreference

class NotificationService:

    @classmethod
    def get_user_preferences(cls, user):
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        return pref

    @classmethod
    def notify_user(cls, user, title, message, notification_type='system', priority='normal', module='System', action_url=None, record_type=None, record_id=None):
        if not user or not user.is_authenticated:
            return None

        pref = cls.get_user_preferences(user)

        # Check preference toggles
        if notification_type in ['low_stock', 'out_of_stock', 'over_stock'] and not (pref.notify_low_stock or pref.notify_out_of_stock):
            return None
        if notification_type == 'purchase' and not pref.notify_purchases:
            return None
        if notification_type == 'transfer' and not pref.notify_transfers:
            return None
        if notification_type == 'ocr' and not pref.notify_ocr:
            return None
        if notification_type == 'backup' and not pref.notify_backups:
            return None
        if notification_type == 'security' and not pref.notify_security:
            return None

        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            module=module,
            action_url=action_url,
            related_record_type=record_type,
            related_record_id=str(record_id) if record_id else None
        )
        return notif

    @classmethod
    def notify_role_or_all(cls, role_name=None, title="", message="", notification_type='system', priority='normal', module='System', action_url=None, record_type=None, record_id=None):
        users = User.objects.filter(is_active=True)
        if role_name:
            users = users.filter(profile__role__name=role_name) | users.filter(is_superuser=True)

        created_notifs = []
        for user in users.distinct():
            n = cls.notify_user(user, title, message, notification_type, priority, module, action_url, record_type, record_id)
            if n:
                created_notifs.append(n)
        return created_notifs

    @classmethod
    def dispatch_stock_alerts(cls):
        # Scan low and out of stock items
        stock_items = WarehouseStock.objects.select_related('product', 'warehouse').all()
        active_users = User.objects.filter(is_active=True)

        alerts_sent = 0
        for item in stock_items:
            is_out = item.quantity == 0
            is_low = item.quantity > 0 and item.quantity <= item.min_stock_level

            if not (is_out or is_low):
                continue

            notif_type = 'out_of_stock' if is_out else 'low_stock'
            priority = 'critical' if is_out else 'high'
            title = f"{'Out of Stock' if is_out else 'Low Stock'} Alert: {item.product.name}"
            msg = f"{item.product.name} (SKU: {item.product.sku}) in '{item.warehouse.name}'. Current Stock: {item.quantity}, Min Required: {item.min_stock_level}."
            action_url = f"/inventory/?warehouse={item.warehouse.id}&search={item.product.sku}"

            for user in active_users:
                # Check warehouse access scoping
                user_warehouses = RBACService.get_user_warehouses(user)
                if user_warehouses is not None:  # None means all warehouses access
                    if item.warehouse not in user_warehouses:
                        continue  # Skip alerting user for unauthorized warehouse

                # Prevent duplicate unread notifications for same item within 24h
                already_exists = Notification.objects.filter(
                    user=user,
                    notification_type=notif_type,
                    related_record_id=str(item.product.id),
                    is_read=False
                ).exists()

                if not already_exists:
                    cls.notify_user(user, title, msg, notification_type=notif_type, priority=priority, module='Inventory', action_url=action_url, record_type='Product', record_id=item.product.id)
                    alerts_sent += 1

        return alerts_sent

    @classmethod
    def mark_as_read(cls, notification_id, user):
        notif = Notification.objects.filter(id=notification_id, user=user).first()
        if notif:
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save()
            return True
        return False

    @classmethod
    def mark_all_read(cls, user):
        Notification.objects.filter(user=user, is_read=False).update(is_read=True, read_at=timezone.now())

    @classmethod
    def get_user_notifications(cls, user):
        if not user or not user.is_authenticated:
            return {'unread_count': 0, 'recent': []}

        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        recent = Notification.objects.filter(user=user)[:15]
        return {
            'unread_count': unread_count,
            'recent': recent
        }
