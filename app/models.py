from datetime import datetime
from . import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(32), unique=True, nullable=False)
    display_name = db.Column(db.String(120))
    default_address = db.Column(db.String(255))
    last_lat = db.Column(db.Float)
    last_lon = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_order_at = db.Column(db.DateTime)
    order_count = db.Column(db.Integer, default=0)
    lifetime_value = db.Column(db.Float, default=0.0)
    blocked = db.Column(db.Boolean, default=False)

class AuthPin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), unique=True, nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    alias = db.Column(db.String(80))
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    name = db.Column(db.String(120))
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(24), default="new")
    assigned_driver = db.Column(db.String(32))
    eta_min = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Driver(db.Model):
    phone = db.Column(db.String(32), primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    status = db.Column(db.String(24), default="available")
    active_orders = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
