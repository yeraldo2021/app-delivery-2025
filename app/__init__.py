import os, secrets
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", secrets.token_hex(16))

    # Normaliza DATABASE_URL si viniera como postgres://
    db_url = os.getenv("DATABASE_URL", "sqlite:///resto.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa DB
    db.init_app(app)

    # Registra modelos para que el metadata exista
    from . import models  # noqa

    # Crea tablas en SQLite (opcional; en Postgres usa migraciones)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"No se pudieron crear tablas automáticamente: {e}")

    # Registra blueprints si cargan; si no, arranca igual
    def try_bp(import_path, attr, url_prefix=None):
        try:
            mod = __import__(import_path, fromlist=[attr])
            bp = getattr(mod, attr)
            app.register_blueprint(bp, url_prefix=url_prefix)
        except Exception as e:
            app.logger.warning(f"Blueprint {import_path}.{attr} no cargó: {e}")

    try_bp("app.api", "api_bp", url_prefix="/api")
    try_bp("app.web.cliente", "cliente_bp", url_prefix=None)
    try_bp("app.web.repartidor", "repartidor_bp", url_prefix=None)
    try_bp("app.web.restaurante", "restaurante_bp", url_prefix=None)

    @app.route("/")
    def index():
        # Si existe el blueprint de cliente, redirige; si no, responde OK
        return redirect(url_for("cliente.cliente")) if "cliente" in app.blueprints else "OK"

    @app.route("/ping")
    def ping():
        return "pong", 200

    return app
