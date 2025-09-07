# app/__init__.py
import os, secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

db = SQLAlchemy()

def _normalize_db_url(u: str) -> str:
    if not u:
        return "sqlite:///resto.db"
    if u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql://", 1)
    if u.startswith("postgresql://"):
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
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_db_url(os.getenv("DATABASE_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Importa modelos para que create_all conozca las tablas
    from . import models  # noqa

    with app.app_context():
        db.create_all()

    # Blueprints (API y páginas)
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # IMPORTANTE: importar el paquete web para que se adjunten las rutas a los blueprints
    from .web import cliente_bp, repartidor_bp, restaurante_bp  # noqa
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

