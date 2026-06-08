from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import DB, User
from ..models import Order
from ..admin_notifications import get_admin_notification

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_submit():
    data = request.json or {}

    user = User.query.filter_by(email=data.get('email', '')).first()
    if not user or not check_password_hash(user.password, data.get('password', '')):
        return jsonify({'message': 'Invalid email or password'}), 401

    session['user_id'] = user.id
    return jsonify({'message': 'Login successful', 'redirect': '/dashboard', 'user': {'username': user.username, 'email': user.email, 'phone': user.phone, 'address': user.address}})


@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')


@auth_bp.route('/register', methods=['POST'])
def register():

    data = request.json or {}

    if User.query.filter_by(email=data.get('email', '')).first():
        return jsonify({'message': 'Email already registered'}), 409

    hashed = generate_password_hash(data['password'])

    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed,
        phone=data.get('phone', ''),
        address=data.get('address', '')
    )

    DB.session.add(user)
    DB.session.commit()

    session['user_id'] = user.id
    return jsonify({'message': 'User Registered', 'redirect': '/dashboard', 'user': {'username': user.username, 'email': user.email, 'phone': user.phone, 'address': user.address}})


@auth_bp.route('/dashboard', methods=['GET'])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('login.html')

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return render_template('login.html')

    # Fetch user's orders and try to enrich with notification details
    orders_q = Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).limit(50).all()
    orders = []
    for o in orders_q:
        note = get_admin_notification(o.id) or {}
        orders.append({
            'id': o.id,
            'status': o.status or note.get('order_status', 'Pending'),
            'total': float(o.total or note.get('order_total') or 0),
            'created_at': note.get('created_at') or None,
            'cart_items': note.get('cart_items') or [],
        })

    return render_template('dashboard.html', user=user, orders=orders)
    return render_template('dashboard.html', user=user)
