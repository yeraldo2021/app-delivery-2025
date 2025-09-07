from flask import Blueprint, redirect, url_for, session
from .cliente import cliente_bp, CLIENTE_HTML
from .repartidor import repartidor_bp, REPARTIDOR_HTML
from .restaurante import restaurante_bp, RESTAURANTE_HTML
from ..base import render_page
from ..utils import MENU

# Cliente
@cliente_bp.route("/cliente")
def cliente():
    from flask import session
    return render_page(CLIENTE_HTML, title="Cliente", tab="c", session=session, phone=session.get("phone",""), menu=MENU)

@cliente_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("cliente.cliente"))

# Repartidor
@repartidor_bp.route("/repartidor")
def repartidor():
    return render_page(REPARTIDOR_HTML, title="Repartidor", tab="r")

# Restaurante
@restaurante_bp.route("/restaurante")
def restaurante():
    return render_page(RESTAURANTE_HTML, title="Restaurante", tab="a")
