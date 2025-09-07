import os, secrets
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Si es Postgres y no trae sslmode, fuerzalo (Railway lo pide)
    if url.startswith("postgresql://") and "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(16))

    db_url = os.getenv("DATABASE_URL", "sqlite:///resto.db")
    db_url = _normalize_db_url(db_url)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Importa modelos para que SQLAlchemy conozca las tablas
    from . import models  # noqa

    # En producción con Postgres, evita crear tablas “a ciegas”.
    # Déjalo activado solo si usas SQLite local o sabes que es seguro:
    if db_url.startswith("sqlite:///"):
        with app.app_context():
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(f"No se pudieron crear tablas automáticamente: {e}")

    # Blueprints (no deben lanzar excepción en import)
    def try_bp(import_path, attr, url_prefix=None):
        try:
            mod = __import__(import_path, fromlist=[attr])
            bp = getattr(mod, attr)
            app.register_blueprint(bp, url_prefix=url_prefix)
        except Exception as e:
            app.logger.warning(f"Blueprint {import_path}.{attr} no cargó: {e}")

    try_bp("app.api", "api_bp", url_prefix="/api")
    try_bp("app.web.cliente", "cliente_bp")
    try_bp("app.web.repartidor", "repartidor_bp")
    try_bp("app.web.restaurante", "restaurante_bp")

    @app.route("/ping")
    def ping():
        return "pong", 200

    @app.route("/")
    def index():
        return "OK"

    return app
