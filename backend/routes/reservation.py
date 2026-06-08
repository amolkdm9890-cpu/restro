from datetime import datetime
import random

from flask import Blueprint, render_template, request, redirect, url_for

from ..models import DB, Reservation

reservation_bp = Blueprint("reservation", __name__)


def _generate_receipt_number():
    return f"RB{int(datetime.utcnow().timestamp())}{random.randint(100,999)}"


@reservation_bp.route("/reservation", methods=["GET", "POST"])
def reservation():
    if request.method == "GET":
        return render_template("reservation.html")

    # POST: create reservation and show receipt
    username = request.form.get("name", "Guest").strip()
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    guests = int(request.form.get("guests", "1") or 1)
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    payment_method = request.form.get("payment_method", "Online")

    # create reservation record
    res = Reservation(username=username, date=date, time=time, guests=guests)
    DB.session.add(res)
    DB.session.commit()

    # assign a friendly table name/number (simple logic)
    table_name = f"Table {100 + (res.id % 12)}"

    # booking charge (simulated)
    booking_fee = float(request.form.get("booking_fee", 150.0))

    receipt = {
        "receipt_no": _generate_receipt_number(),
        "reservation_id": res.id,
        "username": username,
        "date": date,
        "time": time,
        "guests": guests,
        "phone": phone,
        "email": email,
        "table": table_name,
        "booking_fee": booking_fee,
        "payment_method": payment_method,
        "issued_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
    }

    return render_template("reservation_receipt.html", receipt=receipt)
