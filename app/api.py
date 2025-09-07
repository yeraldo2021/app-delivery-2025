from flask import Blueprint, request, jsonify, session
from . import db
from .models import Client, AuthPin, Address, Order, OrderItem, Driver
from .utils import sanitize_phone, looks_valid_phone, hash_pin, haversine_km
from datetime import datetime

api_bp = Blueprint("api", __name__)

def require_session_json():
    cid = session.get("cid")
    return (cid, None) if cid else (None, (jsonify(error="No autorizado"), 401))

# Auth PIN
@api_bp.post("/auth/pin")
def api_create_pin():
    d = request.get_json(force=True)
    phone = sanitize_phone(d.get("phone",""))
    pin = str(d.get("pin","")).strip()
    if not looks_valid_phone(phone) or not (pin.isdigit() and len(pin)==4):
        return jsonify(error="Datos inválidos"), 400
    c = Client.query.filter_by(phone=phone).first()
    if not c:
        c = Client(phone=phone); db.session.add(c); db.session.commit()
    h = hash_pin(phone, pin)
    ap = AuthPin.query.filter_by(client_id=c.id).first()
    if ap: ap.pin_hash = h
    else: db.session.add(AuthPin(client_id=c.id, pin_hash=h))
    db.session.commit()
    return jsonify(ok=True)

@api_bp.post("/auth/verify")
def api_verify_pin():
    d = request.get_json(force=True)
    phone = sanitize_phone(d.get("phone",""))
    pin = str(d.get("pin","")).strip()
    c = Client.query.filter_by(phone=phone).first()
    if not c: return jsonify(ok=False), 401
    ap = AuthPin.query.filter_by(client_id=c.id).first()
    if not ap or ap.pin_hash != hash_pin(phone, pin):
        return jsonify(ok=False), 401
    session["cid"] = c.id
    session["phone"] = phone
    return jsonify(ok=True)

# Direcciones
@api_bp.get("/addresses")
def api_addresses_get():
    cid, err = require_session_json()
    if err: return err
    rows = Address.query.filter_by(client_id=cid).order_by(Address.created_at.desc()).all()
    return jsonify(ok=True, list=[{
        "id":r.id, "alias":r.alias, "address":r.address,
        "lat":r.lat, "lon":r.lon, "is_default":r.is_default
    } for r in rows])

@api_bp.post("/addresses")
def api_addresses_post():
    cid, err = require_session_json()
    if err: return err
    count = Address.query.filter_by(client_id=cid).count()
    if count >= 3: return jsonify(error="Máximo 3 direcciones"), 400
    d = request.get_json(force=True)
    addr = (d.get("address") or "").strip()
    lat, lon = d.get("lat"), d.get("lon")
    if not addr or lat is None or lon is None:
        return jsonify(error="Completa dirección y coordenadas"), 400
    r = Address(client_id=cid, alias=d.get("alias") or "", address=addr, lat=float(lat), lon=float(lon))
    db.session.add(r); db.session.commit()
    return jsonify(ok=True, id=r.id)

@api_bp.put("/addresses")
def api_addresses_put():
    cid, err = require_session_json()
    if err: return err
    d = request.get_json(force=True)
    r = Address.query.filter_by(id=d.get("id"), client_id=cid).first()
    if not r: return jsonify(error="No encontrado"), 404
    r.alias = d.get("alias") or ""
    r.address = d.get("address") or r.address
    r.lat = float(d.get("lat")) if d.get("lat") is not None else r.lat
    r.lon = float(d.get("lon")) if d.get("lon") is not None else r.lon
    db.session.commit()
    return jsonify(ok=True)

@api_bp.delete("/addresses")
def api_addresses_delete():
    cid, err = require_session_json()
    if err: return err
    d = request.get_json(force=True)
    r = Address.query.filter_by(id=d.get("id"), client_id=cid).first()
    if not r: return jsonify(error="No encontrado"), 404
    db.session.delete(r); db.session.commit()
    return jsonify(ok=True)

# Pedidos
@api_bp.get("/orders")
def api_orders_new():
    rows = Order.query.filter_by(status="new").order_by(Order.created_at.desc()).all()
    return jsonify(ok=True, orders=[{
        "id":o.id, "address":o.address, "total":o.total,
        "lat":o.lat, "lon":o.lon, "created_at":o.created_at.isoformat()
    } for o in rows])

@api_bp.get("/orders/all")
def api_orders_all():
    rows = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify(ok=True, orders=[{
        "id":o.id, "status":o.status, "address":o.address, "total":o.total,
        "assigned_driver":o.assigned_driver, "eta_min":o.eta_min,
        "created_at":o.created_at.isoformat()
    } for o in rows])

@api_bp.post("/orders")
def api_orders_create():
    cid, err = require_session_json()
    if err: return err
    d = request.get_json(force=True)
    addr = (d.get("address") or "").strip()
    lat, lon = d.get("lat"), d.get("lon")
    items = d.get("items") or []
    if not addr or lat is None or lon is None or not isinstance(items, list) or not items:
        return jsonify(error="Datos inválidos"), 400
    total = 0.0
    for it in items:
        total += float(it.get("price",0)) * int(it.get("qty",0))
    o = Order(client_id=cid, address=addr, lat=float(lat), lon=float(lon), total=round(total,2))
    db.session.add(o); db.session.flush()
    for it in items:
        if int(it.get("qty",0))>0:
            db.session.add(OrderItem(order_id=o.id, name=it.get("name"), qty=int(it["qty"]), price=float(it.get("price",0))))
    c = Client.query.get(cid)
    c.last_order_at = datetime.utcnow()
    c.order_count = (c.order_count or 0) + 1
    c.lifetime_value = round((c.lifetime_value or 0) + total, 2)
    c.default_address = addr; c.last_lat=float(lat); c.last_lon=float(lon)
    db.session.commit()
    return jsonify(ok=True, order={"id":o.id, "total":o.total})

@api_bp.post("/orders/<int:order_id>/assign")
def api_orders_assign(order_id: int):
    d = request.get_json(force=True)
    driver_phone = sanitize_phone(d.get("driver_phone",""))
    if not driver_phone: return jsonify(error="driver_phone requerido"), 400
    o = Order.query.get(order_id)
    if not o: return jsonify(error="Pedido no existe"), 404
    if o.status != "new": return jsonify(error="Pedido ya tomado"), 400
    drv = Driver.query.filter_by(phone=driver_phone).first()
    if not drv:
        drv = Driver(phone=driver_phone)
        db.session.add(drv); db.session.commit()
    eta = None
    if drv.lat is not None and drv.lon is not None:
        dist = haversine_km(drv.lat, drv.lon, o.lat, o.lon)
        eta = int(round((dist/25.0)*60))
    o.status = "assigned"; o.assigned_driver = driver_phone; o.eta_min = eta
    drv.active_orders = (drv.active_orders or 0) + 1
    drv.status = "busy"
    db.session.commit()
    return jsonify(ok=True, order_id=o.id, eta_min=eta)

@api_bp.post("/orders/<int:order_id>/deliver")
def api_orders_deliver(order_id: int):
    o = Order.query.get(order_id)
    if not o: return jsonify(error="Pedido no existe"), 404
    o.status = "delivered"
    if o.assigned_driver:
        drv = Driver.query.filter_by(phone=o.assigned_driver).first()
        if drv:
            drv.active_orders = max((drv.active_orders or 1)-1, 0)
            drv.status = "available" if drv.active_orders == 0 else "busy"
    db.session.commit()
    return jsonify(ok=True)

# Drivers
@api_bp.get("/drivers")
def api_drivers_get():
    rows = Driver.query.order_by(Driver.updated_at.desc()).all()
    return jsonify(ok=True, list=[{
        "phone":r.phone, "lat":r.lat, "lon":r.lon, "status":r.status,
        "active_orders":r.active_orders, "updated_at": (r.updated_at or datetime.now()).isoformat()
    } for r in rows])

@api_bp.put("/drivers")
def api_driver_loc():
    d = request.get_json(force=True)
    phone = sanitize_phone(d.get("phone",""))
    if not phone: return jsonify(error="phone requerido"), 400
    drv = Driver.query.filter_by(phone=phone).first()
    if not drv:
        drv = Driver(phone=phone)
        db.session.add(drv)
    if d.get("lat") is not None: drv.lat = float(d.get("lat"))
    if d.get("lon") is not None: drv.lon = float(d.get("lon"))
    db.session.commit()
    return jsonify(ok=True)
