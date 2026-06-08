import math
import time
from datetime import datetime, timedelta


STAGE_SEQUENCE = [
    "pending_confirmation",
    "confirmed",
    "preparing",
    "packed",
    "out_for_delivery",
    "delivered",
]

STAGE_BASE_MINUTES = {
    "pending_confirmation": 28,
    "confirmed": 22,
    "preparing": 16,
    "packed": 10,
    "out_for_delivery": 5,
    "delivered": 0,
}


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _stage_key_for_status(status):
    normalized = (status or "").strip().lower()
    if normalized.startswith("pending"):
        return "pending_confirmation"
    if normalized.startswith("confirm") or normalized == "paid":
        return "confirmed"
    if normalized.startswith("prepar"):
        return "preparing"
    if normalized.startswith("pack"):
        return "packed"
    if normalized.startswith("out"):
        return "out_for_delivery"
    if normalized.startswith("deliver"):
        return "delivered"
    return "confirmed"


def _parse_timestamp(value):
    if not value:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return datetime.fromisoformat(str(value)).timestamp()
    except (TypeError, ValueError):
        return None


def _count_items(cart_items):
    if not isinstance(cart_items, list):
        return 0
    return len(cart_items)


def _estimate_stage_minutes(stage_key, elapsed_minutes):
    stage_base = STAGE_BASE_MINUTES.get(stage_key, 20)
    return max(0, stage_base - max(0, elapsed_minutes * 0.55))


def predict_order_eta(order, checkout_details=None, cart_items=None, payment_method="", active_tracking=None, notification=None):
    checkout_details = checkout_details or {}
    cart_items = cart_items or []
    active_tracking = active_tracking or {}
    notification = notification or {}

    total = _safe_float(getattr(order, "total", 0), 0.0)
    item_count = _count_items(cart_items)
    address = str(checkout_details.get("address") or "").strip()
    order_status = getattr(order, "status", "") or notification.get("order_status") or ""
    stage_key = _stage_key_for_status(order_status)

    started_at = _parse_timestamp(active_tracking.get("started_at"))
    confirmed_at = _parse_timestamp(notification.get("confirmed_at"))
    if started_at is None:
        started_at = confirmed_at or time.time()

    elapsed_minutes = max(0, int((time.time() - started_at) / 60))

    hour = datetime.now().hour
    weekday = datetime.now().weekday()
    is_weekend = weekday >= 5
    lunch_peak = 12 <= hour < 15
    dinner_peak = 19 <= hour < 22
    late_night = hour >= 22 or hour < 6
    payment_is_online = str(payment_method or notification.get("payment_method") or "").strip().lower() == "online payment"

    base_minutes = 18.0
    base_minutes += item_count * 2.7
    base_minutes += total * 0.028
    base_minutes += min(8.0, max(0, len(address) - 18) * 0.08)
    base_minutes += _estimate_stage_minutes(stage_key, elapsed_minutes)

    if payment_is_online and stage_key == "pending_confirmation":
        base_minutes += 6.0
    elif payment_is_online:
        base_minutes += 2.0

    if is_weekend:
        base_minutes += 4.0
    if lunch_peak or dinner_peak:
        base_minutes += 3.5
    if late_night:
        base_minutes -= 2.0

    predicted_total_minutes = max(elapsed_minutes + 4, int(round(base_minutes)))
    predicted_remaining_minutes = max(0, predicted_total_minutes - elapsed_minutes)
    predicted_completion_at = datetime.now() + timedelta(minutes=predicted_remaining_minutes)

    uncertainty = 0.26
    if item_count >= 5:
        uncertainty += 0.06
    if total >= 500:
        uncertainty += 0.04
    if not address:
        uncertainty += 0.05
    if payment_is_online:
        uncertainty += 0.03
    if stage_key == "pending_confirmation":
        uncertainty += 0.05
    if is_weekend:
        uncertainty += 0.03
    if lunch_peak or dinner_peak:
        uncertainty += 0.03

    confidence = max(0.58, min(0.94, 1.0 - uncertainty))

    if stage_key == "pending_confirmation":
        insight = "AI estimates extra confirmation time before the kitchen starts prep."
    elif stage_key == "confirmed":
        insight = "AI is balancing basket size and payment mode to refine the ETA."
    elif stage_key == "preparing":
        insight = "Kitchen prep is underway, so the ETA is tightening from live stage progress."
    elif stage_key == "packed":
        insight = "Packing is nearly complete, so the remaining time is mostly rider dispatch."
    elif stage_key == "out_for_delivery":
        insight = "The rider is on the move and the AI is shortening the remaining delivery window."
    else:
        insight = "The order is complete and the model is learning from the full delivery cycle."

    return {
        "model_name": "Adaptive ETA Predictor",
        "model_version": "v1",
        "stage_key": stage_key,
        "item_count": item_count,
        "predicted_total_minutes": predicted_total_minutes,
        "predicted_remaining_minutes": predicted_remaining_minutes,
        "predicted_completion_time": predicted_completion_at.strftime("%I:%M %p"),
        "confidence": round(confidence, 2),
        "insight": insight,
        "elapsed_minutes": elapsed_minutes,
    }