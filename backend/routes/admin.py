from flask import Blueprint, redirect, render_template, url_for, request, session, current_app

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ..admin_notifications import confirm_admin_notification, load_admin_notifications
from ..models import DB, Order, Reservation, Food

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin.admin"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == current_app.config.get("ADMIN_USERNAME") and password == current_app.config.get("ADMIN_PASSWORD"):
            session["is_admin"] = True
            return redirect(url_for("admin.admin"))
        error = "Invalid credentials"

    return render_template("admin_login.html", error=error)


@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin.admin_login"))

    notifications = load_admin_notifications()
    pending_notifications = [item for item in notifications if item.get("status") != "confirmed"]
    confirmed_notifications = [item for item in notifications if item.get("status") == "confirmed"]

    total_orders = Order.query.count()
    total_revenue = DB.session.query(DB.func.sum(Order.total)).scalar() or 0

    # Reservations
    total_reservations = Reservation.query.count()
    recent_reservations = Reservation.query.order_by(Reservation.id.desc()).limit(8).all()

    # Sales by day (from admin_notifications created_at)
    notifications_all = load_admin_notifications()
    sales_by_day = defaultdict(float)
    recent_orders = []
    product_counter = Counter()
    for n in notifications_all:
        created = n.get("created_at")
        try:
            date_key = datetime.fromisoformat(created).date().isoformat() if created else None
        except Exception:
            date_key = None

        order_total = float(n.get("order_total") or 0)
        if date_key:
            sales_by_day[date_key] += order_total

        recent_orders.append(n)
        for item in (n.get("cart_items") or []):
            # items stored as dicts with `name` key in notifications
            name = item.get("name") or item.get("title") or str(item)
            product_counter[name] += int(item.get("quantity", 1)) if isinstance(item, dict) else 1

    # Prepare last 7 days list (descending)
    last_7 = []
    for i in range(6, -1, -1):
        d = (datetime.utcnow().date() - timedelta(days=i)).isoformat()
        last_7.append({"date": d, "sales": sales_by_day.get(d, 0.0)})

    # Top products
    top_products = product_counter.most_common(8)

    # Recent online orders (limit)
    recent_orders = recent_orders[:12]

    return render_template(
        "admin.html",
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_users=0,
        total_reservations=total_reservations,
        recent_reservations=recent_reservations,
        daily_sales=last_7,
        top_products=top_products,
        recent_orders=recent_orders,
        pending_notifications=pending_notifications,
        confirmed_notifications=confirmed_notifications,
    )


@admin_bp.route("/admin/orders/<int:order_id>/confirm", methods=["POST"])
def confirm_order(order_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin.admin_login"))

    order = Order.query.get_or_404(order_id)
    order.status = "Confirmed"
    DB.session.commit()
    confirm_admin_notification(order_id)
    return redirect(url_for("admin.admin"))
