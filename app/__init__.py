# app/__init__.py
import os, secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

db = SQLAlchemy()

def _normalize_db_url(u: str) -> str:
    if not u:
        return "sqlite:///resto.db"
    # postgres:// -> postgresql://
    if u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql://", 1)
    if u.startswith("postgresql://"):
        # añade sslmode=require si no está
        parts = urlparse(u)
        q = parse_qs(parts.query)
        if "sslmode" not in q:
            q["sslmode"] = ["require"]
            parts = parts._replace(query=urlencode(q, doseq=True))
            u = urlunparse(parts)
    return u

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(16))

    raw = os.getenv("DATABASE_URL", "sqlite:///resto.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_db_url(raw)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from . import models  # registra modelos

    with app.app_context():
        db.create_all()  # crea tablas si no existen

    from .api import api_bp
    from .web.cliente import cliente_bp
    from .web.repartidor import repartidor_bp
    from .web.restaurante import restaurante_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(cliente_bp)
    app.register_blueprint(repartidor_bp)
    app.register_blueprint(restaurante_bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("cliente.cliente"))

    @app.route("/ping")
    def ping(): return "pong"

    return app
