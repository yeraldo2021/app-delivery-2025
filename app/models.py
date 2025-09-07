from datetime import datetime
from . import db

class Client(db.Model):
    __tablename__ = "clients"
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

    addresses = db.relationship("Address", backref="client", lazy=True, cascade="all, delete-orphan")
    pins = db.relationship("AuthPin", backref="client", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="client", lazy=True)

class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    label = db.Column(db.String(64))             # ej. "Casa", "Trabajo"
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuthPin(db.Model):
    __tablename__ = "auth_pins"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    pin_hash = db.Column(db.String(64), nullable=False)  # sha256
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(24), default="new")      # new, assigned, delivering, done, canceled
    assigned_driver = db.Column(db.String(32))
    eta_min = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)

class Driver(db.Model):
    __tablename__ = "drivers"
    phone = db.Column(db.String(32), primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    status = db.Column(db.String(24), default="available")   # available, busy, offline
    active_orders = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
