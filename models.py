from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='intern')  # 'intern' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Seat(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default='available')  # available / unavailable

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active')  # active / cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reservations')
    seat = db.relationship('Seat', backref='reservations')