import base64
import io
import json
import time
from datetime import datetime

import qrcode
import urllib.parse

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from ..admin_notifications import (
    confirm_admin_notification,
    get_admin_notification,
    queue_admin_notification,
    mark_paid_notification,
)
from ..order_eta_ai import predict_order_eta
from ..models import DB, Order, User

orders_bp = Blueprint("orders", __name__)


def build_route_map_url(delivery_address, restaurant_address):
    delivery_address = (delivery_address or "").strip()
    restaurant_address = (restaurant_address or "").strip()

    if delivery_address and restaurant_address:
        origin = urllib.parse.quote_plus(restaurant_address)
        destination = urllib.parse.quote_plus(delivery_address)
        return f"https://www.google.com/maps?output=embed&saddr={origin}&daddr={destination}"

    if delivery_address:
        destination = urllib.parse.quote_plus(delivery_address)
        return f"https://www.google.com/maps?q={destination}&output=embed"

    if restaurant_address:
        origin = urllib.parse.quote_plus(restaurant_address)
        return f"https://www.google.com/maps?q={origin}&output=embed"

    return "https://www.google.com/maps?q=Food%20Express%20Restaurant&output=embed"


def build_checkout_context(checkout_details=None, cart_items=None, order_total=0, order_error=None, order_success=None):
    return {
        "checkout_details": checkout_details or {
            "full_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "payment_method": "Cash on Delivery",
        },
        "cart_items": cart_items or [],
        "order_total": order_total,
        "order_error": order_error,
        "order_success": order_success,
    }


def generate_payment_qr(order_total, order_reference):
    # Build UPI params and URL-encode them to ensure valid QR payload
    params = {
        'pa': '7822065495@upi',
        'pn': 'Food Express',
        'am': f"{order_total:.2f}",
        'cu': 'INR',
        'tn': f"Food Express Order {order_reference}",
    }

    payment_uri = 'upi://pay?' + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    # log the generated URI for debugging (not printed to users)
    try:
        # Flask logger may not be available in this module at import, use print as fallback
        from flask import current_app
        if current_app:
            current_app.logger.debug(f'Generated payment URI: {payment_uri}')
    except Exception:
        try:
            print('Generated payment URI:', payment_uri)
        except Exception:
            pass

    # Increase box_size/border for more reliable scanning on small displays
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(payment_uri)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def build_tracking_payload(order_id):
    order = Order.query.get(order_id)
    active_tracking = session.get("active_tracking") or {}
    notification = get_admin_notification(order_id) or {}
    checkout_details = active_tracking.get("checkout_details") or notification.get("checkout_details") or {}
    delivery_address = checkout_details.get("address", "")
    delivery_lat = checkout_details.get("latitude") or checkout_details.get("lat")
    delivery_lng = checkout_details.get("longitude") or checkout_details.get("lng")
    restaurant_address = current_app.config.get("RESTAURANT_ADDRESS", "Food Express Kitchen")
    cart_items = active_tracking.get("cart_items") or notification.get("cart_items") or []
    payment_method = notification.get("payment_method") or active_tracking.get("payment_method") or ""

    prediction = predict_order_eta(
        order=order,
        checkout_details=checkout_details,
        cart_items=cart_items,
        payment_method=payment_method,
        active_tracking=active_tracking,
        notification=notification,
    )

    if not order:
        return {
            "order_id": order_id,
            "status": "Order not found",
            "detail": "We could not find this order yet.",
            "progress": 0,
            "eta_minutes": 0,
            "ai_eta_minutes": 0,
            "ai_remaining_minutes": 0,
            "ai_confidence": 0,
            "ai_prediction": prediction,
            "delivery_address": delivery_address,
            "restaurant_address": restaurant_address,
            "driver": {"name": "Food Express", "vehicle": "Awaiting order", "avatar": "FE"},
            "restaurant_name": "Food Express Kitchen",
            "restaurant_note": "Your order is not available yet.",
            "rider_progress": 0,
            "map_url": build_route_map_url(delivery_address, restaurant_address) if not (delivery_lat and delivery_lng) else f"https://www.google.com/maps?output=embed&q={urllib.parse.quote_plus(f'{delivery_lat},{delivery_lng}')}",
            "elapsed_seconds": 0,
            "stages": [{"key": "missing", "label": "Order missing", "detail": "Please refresh after placing an order."}],
            "current_stage_index": 0,
            "updated_at": datetime.now().strftime("%I:%M %p"),
        }

    if (order.status or "").lower().startswith("pending"):
        map_url = build_route_map_url(delivery_address, restaurant_address) if not (delivery_lat and delivery_lng) else f"https://www.google.com/maps?output=embed&q={urllib.parse.quote_plus(f'{delivery_lat},{delivery_lng}')}",

        return {
            "order_id": order_id,
            "status": "Awaiting admin confirmation",
            "detail": "Your order has been sent to the admin for approval.",
            "progress": 0,
            "eta_minutes": 0,
            "ai_eta_minutes": prediction["predicted_total_minutes"],
            "ai_remaining_minutes": prediction["predicted_remaining_minutes"],
            "ai_confidence": prediction["confidence"],
            "ai_prediction": prediction,
            "delivery_address": delivery_address,
            "restaurant_address": restaurant_address,
            "driver": {"name": "Admin review pending", "vehicle": "Waiting for approval", "avatar": "AD"},
            "restaurant_name": "Food Express Kitchen",
            "restaurant_note": "The admin must confirm this order before delivery starts.",
            "rider_progress": 0,
            "map_url": map_url,
            "elapsed_seconds": 0,
            "stages": [
                {"key": "pending_confirmation", "label": "Sent to admin", "detail": "The admin is reviewing your order."},
                {"key": "confirmed", "label": "Order confirmed", "detail": "Payment received and order confirmed."},
                {"key": "preparing", "label": "Preparing food", "detail": "Kitchen is preparing your meal."},
                {"key": "packed", "label": "Packed", "detail": "Your order is packed and ready to go."},
                {"key": "out_for_delivery", "label": "Out for delivery", "detail": "Rider is on the way to your address."},
                {"key": "delivered", "label": "Delivered", "detail": "Your order has been delivered."},
            ],
            "current_stage_index": 0,
            "updated_at": datetime.now().strftime("%I:%M %p"),
        }

    started_at = active_tracking.get("started_at")
    confirmed_at = notification.get("confirmed_at")
    if not started_at and confirmed_at:
        try:
            started_at = datetime.fromisoformat(confirmed_at).timestamp()
        except ValueError:
            started_at = time.time()
        active_tracking["started_at"] = started_at
        session["active_tracking"] = active_tracking

    if not started_at:
        started_at = time.time()
        active_tracking["started_at"] = started_at
        session["active_tracking"] = active_tracking

    elapsed_seconds = max(0, int(time.time() - float(started_at)))
    stages = [
        {"key": "confirmed", "label": "Order confirmed", "detail": "Payment received and order confirmed."},
        {"key": "preparing", "label": "Preparing food", "detail": "Kitchen is preparing your meal."},
        {"key": "packed", "label": "Packed", "detail": "Your order is packed and ready to go."},
        {"key": "out_for_delivery", "label": "Out for delivery", "detail": "Rider is on the way to your address."},
        {"key": "delivered", "label": "Delivered", "detail": "Your order has been delivered."},
    ]
    stage_index = min(elapsed_seconds // 12, len(stages) - 1)
    progress = int((stage_index / (len(stages) - 1)) * 100) if len(stages) > 1 else 100
    eta_minutes = max(0, [28, 20, 12, 6, 0][stage_index] - (elapsed_seconds % 12) // 3)

    drivers = [
        {"name": "Aman Sharma", "vehicle": "Hero Splendor • MH 12 AB 2456", "avatar": "AS"},
        {"name": "Priya Mehta", "vehicle": "Honda Activa • MH 14 XY 8042", "avatar": "PM"},
        {"name": "Rohit Singh", "vehicle": "TVS Jupiter • MH 01 KL 7788", "avatar": "RS"},
    ]
    driver = drivers[order_id % len(drivers)]
    rider_progress = min(100, 18 + stage_index * 20 + (elapsed_seconds % 12) * 2)

    map_url = build_route_map_url(delivery_address, restaurant_address) if not (delivery_lat and delivery_lng) else f"https://www.google.com/maps?output=embed&q={urllib.parse.quote_plus(f'{delivery_lat},{delivery_lng}')}",

    return {
        "order_id": order_id,
        "status": stages[stage_index]["label"],
        "detail": stages[stage_index]["detail"],
        "progress": progress,
        "eta_minutes": eta_minutes,
        "ai_eta_minutes": prediction["predicted_total_minutes"],
        "ai_remaining_minutes": prediction["predicted_remaining_minutes"],
        "ai_confidence": prediction["confidence"],
        "ai_prediction": prediction,
        "delivery_address": delivery_address,
        "restaurant_address": restaurant_address,
        "driver": driver,
        "restaurant_name": "Food Express Kitchen",
        "restaurant_note": "Packed and dispatched from our nearest kitchen.",
        "rider_progress": rider_progress,
        "map_url": map_url,
        "elapsed_seconds": elapsed_seconds,
        "stages": stages,
        "current_stage_index": stage_index,
        "updated_at": datetime.now().strftime("%I:%M %p"),
    }


@orders_bp.route("/cart")
def cart():
    return render_template("cart.html")


@orders_bp.route("/checkout")
def checkout():
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)

    checkout_details = {
        "full_name": user.username if user else "",
        "email": user.email if user else "",
        "phone": user.phone if user and user.phone else "",
        "address": user.address if user and user.address else "",
        "payment_method": "Cash on Delivery",
    }

    return render_template("checkout.html", **build_checkout_context(checkout_details=checkout_details))


@orders_bp.route("/checkout", methods=["POST"])
def checkout_submit():
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    location_confirmed = request.form.get("location_confirmed", "false").lower() == 'true'
    payment_method = request.form.get("payment_method", "").strip()
    cart_payload = request.form.get("cart_payload", "")

    checkout_details = {
        "full_name": full_name or (user.username if user else ""),
        "email": email or (user.email if user else ""),
        "phone": phone or (user.phone if user else ""),
        "address": address or (user.address if user else ""),
        "latitude": latitude or None,
        "longitude": longitude or None,
        "location_confirmed": bool(location_confirmed),
        "payment_method": payment_method,
    }

    if not all([checkout_details["full_name"], checkout_details["email"], checkout_details["phone"], checkout_details["address"], checkout_details["payment_method"]]):
        return render_template(
            "checkout.html",
            **build_checkout_context(
                checkout_details=checkout_details,
                order_error="Please fill in all checkout details before placing the order.",
            ),
        )

    try:
        cart_items = json.loads(cart_payload) if cart_payload else []
    except json.JSONDecodeError:
        cart_items = []

    if not cart_items:
        return render_template(
            "checkout.html",
            **build_checkout_context(
                checkout_details=checkout_details,
                order_error="Your cart is empty. Add items before placing an order.",
            ),
        )

    order_total = sum(float(item.get("price", 0)) for item in cart_items)
    order_reference = f"FE{session.get('user_id', 'guest')}{len(cart_items)}"

    session["pending_checkout"] = {
        "checkout_details": checkout_details,
        "cart_items": cart_items,
        "order_total": order_total,
        "payment_method": payment_method,
    }

    payment_qr = None
    payment_message = ""

    if payment_method == "Online Payment":
        # create an order record so we can track/payment-verify it
        order = Order(user_id=user.id if user else None, total=order_total, status="Pending Confirmation")
        DB.session.add(order)
        DB.session.commit()
        queue_admin_notification(order.id, checkout_details, cart_items, order_total, payment_method, order.status)

        order_reference = f"FE{order.id}{len(cart_items)}"
        payment_qr = generate_payment_qr(order_total, order_reference)
        payment_message = "Scan the QR code to complete your online payment."
        # If this is an AJAX request, return JSON so client can render QR without full page reload
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")
        if is_ajax:
            return jsonify({
                "payment_qr": payment_qr,
                "payment_reference": order_reference,
                "order_total": order_total,
                "payment_mode": payment_method,
                "order_id": order.id,
            })
        # If this is an AJAX request, return JSON so client can render QR without full page reload
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")
        if is_ajax:
            return jsonify({
                "payment_qr": payment_qr,
                "payment_reference": order_reference,
                "order_total": order_total,
                "payment_mode": payment_method,
            })
    else:
        order = Order(user_id=user.id if user else None, total=order_total, status="Pending Confirmation")
        DB.session.add(order)
        DB.session.commit()
        queue_admin_notification(order.id, checkout_details, cart_items, order_total, payment_method, order.status)
        session["active_tracking"] = {
            "order_id": order.id,
            "checkout_details": checkout_details,
            "cart_items": cart_items,
            "order_total": order_total,
            "payment_method": payment_method,
        }
        session.pop("pending_checkout", None)
        session.pop("cart", None)
        return redirect(url_for("orders.track_order", order_id=order.id))

    return render_template(
        "checkout.html",
        **build_checkout_context(
            checkout_details=checkout_details,
            cart_items=cart_items,
            order_total=order_total,
            order_success=payment_message,
        ),
        payment_qr=payment_qr,
        payment_reference=order_reference,
        payment_mode=payment_method,
    )


@orders_bp.route("/checkout/confirm", methods=["POST"])
def checkout_confirm():
    pending_checkout = session.get("pending_checkout")
    snapshot = None
    snapshot_raw = request.form.get("checkout_snapshot", "")
    if snapshot_raw:
        try:
            snapshot = json.loads(snapshot_raw)
        except json.JSONDecodeError:
            snapshot = None

    if not pending_checkout:
        if not snapshot:
            return render_template(
                "checkout.html",
                **build_checkout_context(order_error="No pending payment found. Please place the order again."),
            )

    user = None
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)

    checkout_details = pending_checkout.get("checkout_details", {}) if pending_checkout else snapshot.get("checkout_details", {})
    cart_items = pending_checkout.get("cart_items", []) if pending_checkout else snapshot.get("cart_items", [])
    order_total = pending_checkout.get("order_total", 0) if pending_checkout else snapshot.get("order_total", 0)
    payment_method = pending_checkout.get("payment_method", "Online Payment") if pending_checkout else snapshot.get("payment_method", "Online Payment")

    order = Order(
        user_id=user.id if user else None,
        total=order_total,
        status="Pending Confirmation",
    )
    DB.session.add(order)
    DB.session.commit()
    queue_admin_notification(order.id, checkout_details, cart_items, order_total, payment_method, order.status)

    # Move user to active tracking and clear pending
    session["active_tracking"] = {
        "order_id": order.id,
        "checkout_details": checkout_details,
        "cart_items": cart_items,
        "order_total": order_total,
        "payment_method": payment_method,
    }
    session.pop("pending_checkout", None)
    session.pop("cart", None)

    return redirect(url_for("orders.track_order", order_id=order.id))
