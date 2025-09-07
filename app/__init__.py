import os, secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", secrets.token_hex(16))

    # Normaliza DATABASE_URL si viene como postgres://
    db_url = os.getenv("DATABASE_URL", "sqlite:///resto.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importa modelos para db.create_all
    from . import models  # noqa

    with app.app_context():
        db.create_all()

    # Registra blueprints
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
