# app.py — Flask + SQLAlchemy (Cliente / Repartidor / Restaurante) — listo para Railway
import os, math, hashlib, secrets
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///resto.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_count = db.Column(db.Integer, default=0)
    lifetime_value = db.Column(db.Float, default=0.0)

class AuthPin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), unique=True, nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    address = db.Column(db.String(255))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    total = db.Column(db.Float)
    status = db.Column(db.String(24), default="new")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Driver(db.Model):
    phone = db.Column(db.String(32), primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    status = db.Column(db.String(24), default="available")
    active_orders = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "<h2>✅ App corriendo. Usa /cliente, /repartidor o /restaurante</h2>"

@app.route("/cliente")
def cliente():
    return "<h1>🧑‍🍳 Cliente</h1>"

@app.route("/repartidor")
def repartidor():
    return "<h1>🚴 Repartidor</h1>"

@app.route("/restaurante")
def restaurante():
    return "<h1>🏪 Restaurante</h1>"

@app.route("/ping")
def ping(): return "pong"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
