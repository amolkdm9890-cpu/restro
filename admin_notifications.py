import json
from datetime import datetime
from pathlib import Path


NOTIFICATION_FILE = Path(__file__).resolve().parent / "admin_notifications.json"


def load_admin_notifications():
    if not NOTIFICATION_FILE.exists():
        return []

    try:
        with NOTIFICATION_FILE.open("r", encoding="utf-8") as file_handle:
            notifications = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return []

    return notifications if isinstance(notifications, list) else []


def save_admin_notifications(notifications):
    with NOTIFICATION_FILE.open("w", encoding="utf-8") as file_handle:
        json.dump(notifications, file_handle, indent=2)


def queue_admin_notification(order_id, checkout_details, cart_items, order_total, payment_method, order_status):
    notifications = load_admin_notifications()
    notification = {
        "order_id": order_id,
        "status": "pending",
        "order_status": order_status,
        "checkout_details": checkout_details,
        "cart_items": cart_items,
        "order_total": order_total,
        "payment_method": payment_method,
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        "confirmed_at": None,
    }

    notifications = [item for item in notifications if item.get("order_id") != order_id]
    notifications.insert(0, notification)
    save_admin_notifications(notifications)
    return notification


def get_admin_notification(order_id):
    for notification in load_admin_notifications():
        if notification.get("order_id") == order_id:
            return notification
    return None


def confirm_admin_notification(order_id):
    notifications = load_admin_notifications()
    confirmed_at = datetime.utcnow().isoformat(timespec="seconds")
    updated = False

    for notification in notifications:
        if notification.get("order_id") == order_id:
            notification["status"] = "confirmed"
            notification["confirmed_at"] = confirmed_at
            updated = True
            break

    if updated:
        save_admin_notifications(notifications)

    return updated


def mark_paid_notification(order_id):
    notifications = load_admin_notifications()
    paid_at = datetime.utcnow().isoformat(timespec="seconds")
    updated = False

    for notification in notifications:
        if notification.get("order_id") == order_id:
            notification["order_status"] = "Paid"
            notification["paid_at"] = paid_at
            updated = True
            break

    if updated:
        save_admin_notifications(notifications)

    return updated
