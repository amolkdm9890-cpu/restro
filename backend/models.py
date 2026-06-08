from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()

class User(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(100))
    email = DB.Column(DB.String(100), unique=True)
    password = DB.Column(DB.String(300))
    phone = DB.Column(DB.String(20))
    address = DB.Column(DB.String(300))

class Food(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(100))
    category = DB.Column(DB.String(100))
    price = DB.Column(DB.Float)
    image = DB.Column(DB.String(500))
    description = DB.Column(DB.Text)

class Order(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    user_id = DB.Column(DB.Integer)
    total = DB.Column(DB.Float)
    status = DB.Column(DB.String(100))

class Reservation(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(100))
    date = DB.Column(DB.String(100))
    time = DB.Column(DB.String(100))
    guests = DB.Column(DB.Integer)