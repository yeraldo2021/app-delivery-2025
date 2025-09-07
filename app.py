# app.py — Flask + SQLAlchemy (Cliente / Repartidor / Restaurante) — Railway
import os, math, hashlib, secrets
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///resto.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --------------------- Modelos ---------------------
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
    status = db.Column(db.String(24), default="new")  # new/assigned/delivered/cancelled
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

with app.app_context():
    db.create_all()

# --------------------- Utilidades ---------------------
MENU = {
    'Chaufa': 18.0,
    'Tallarín saltado': 20.0,
    'Wantán frito (10u)': 12.0,
    'Pollo a la brasa (1/4)': 19.0,
    'Inka Kola 500ml': 5.0,
}

def sanitize_phone(s: str) -> str:
    if not s: return ""
    t = ''.join(ch for ch in s if ch.isdigit() or ch=='+')
    if t.startswith('+'): return t
    d = ''.join(ch for ch in t if ch.isdigit())
    return '+51' + d if d else ""

def looks_valid_phone(ph: str) -> bool:
    d = ''.join(ch for ch in (ph or '') if ch.isdigit())
    if d.startswith("51"): return len(d) == 11
    return len(d) == 9

def hash_pin(e164: str, pin4: str) -> str:
    return hashlib.sha256((e164 + ":" + pin4).encode()).hexdigest()

def haversine_km(lat1, lon1, lat2, lon2):
    import math
    R=6371.0
    p1=math.radians(lat1); p2=math.radians(lat2)
    dphi=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dphi/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1, math.sqrt(a)))

# --------------------- Plantilla base ---------------------
BASE_SHELL = """
<!doctype html>
<html lang="es"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{{ title }}</title>
<link rel="stylesheet" href="https://unpkg.com/modern-css-reset/dist/reset.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<style>
 body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;background:#f8fafc;color:#0f172a}
 .container{max-width:1080px;margin:0 auto;padding:20px}
 .card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;box-shadow:0 10px 24px rgba(2,6,23,.05);padding:16px;margin:14px 0}
 h1{font-size:22px;margin-bottom:10px} h2{font-size:18px;margin:8px 0}
 input,button{border:1px solid #cbd5e1;border-radius:10px;padding:10px}
 button{background:#0f172a;color:#fff;cursor:pointer}
 button.secondary{background:#e2e8f0;color:#0f172a}
 .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
 .list{border:1px solid #e2e8f0;border-radius:12px;overflow:hidden}
 .item{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:10px;border-top:1px solid #f1f5f9}
 .item:first-child{border-top:none}
 .badge{font-size:12px;color:#64748b}
 nav a{margin-right:10px;text-decoration:none;color:#0f172a}
 nav a.active{text-decoration:underline}
 #map,#dmap{height:420px;border-radius:14px;background:#e2e8f0}
 table{width:100%;border-collapse:collapse} th,td{border-bottom:1px solid #e2e8f0;padding:8px;text-align:left}
</style>
</head><body>
<div class="container">
  <nav>
    <a href="{{ url_for('cliente') }}" class="{{ 'active' if tab=='c' else '' }}">Cliente</a>
    <a href="{{ url_for('repartidor') }}" class="{{ 'active' if tab=='r' else '' }}">Repartidor</a>
    <a href="{{ url_for('restaurante') }}" class="{{ 'active' if tab=='a' else '' }}">Restaurante</a>
    {% if session.get('cid') %} <a href="{{ url_for('logout') }}">Cerrar sesión</a> {% endif %}
  </nav>
  {{ content|safe }}
</div>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
</body></html>
"""

def render_page(content_html: str, **ctx):
    # 1) Renderiza el contenido con su propio contexto (para que funcionen {{ ... }} y {% ... %})
    inner = render_template_string(content_html, **ctx)
    # 2) Inserta el resultado en la carcasa/base
    return render_template_string(BASE_SHELL, content=inner, **ctx)

# --------------------- “Páginas” (contenido) ---------------------
CLIENTE_HTML = """
<div class="card">
  <h1>🧑‍🍳 Cliente – Haz tu pedido</h1>
  <div class="row">
    <div><label>Teléfono</label><input id="phone" placeholder="+51 999 999 999" value="{{ phone or '' }}" /></div>
    <div><label>PIN (4)</label><input id="pin" maxlength="4" placeholder="****" /></div>
  </div>
  <div style="margin-top:10px;display:flex;gap:8px">
    <button onclick="createPin()">Crear PIN</button>
    <button onclick="verifyPin()">Verificar PIN</button>
    {% if session.get('cid') %}<span class="badge">✅ Sesión activa</span>{% endif %}
  </div>
</div>

<div class="card">
  <h2>Dirección y mapa</h2>
  <input id="address" placeholder="Av. 15 de Julio 123, Lima" />
  <div id="map" style="margin-top:8px"></div>
  <div class="badge" id="coords">Coords: — , —</div>

  <div class="row" style="margin-top:10px">
    <div><label>Alias</label><input id="alias" placeholder="Casa / Trabajo" /></div>
    <div style="display:flex;gap:8px;align-items:end">
      <button onclick="saveAddress()">💾 Guardar / Actualizar</button>
      <button class="secondary" onclick="clearSel()">Limpiar selección</button>
    </div>
  </div>

  <div class="list" id="addrList" style="margin-top:10px"></div>
</div>

<div class="card">
  <h2>Menú y cantidades</h2>
  <div id="menu"></div>
  <div style="text-align:right;margin-top:10px"><b>Total: S/ <span id="total">0.00</span></b></div>
  <button style="width:100%;margin-top:10px" onclick="placeOrder()">✅ Enviar pedido</button>
  <span class="badge">Verifica PIN y fija coordenadas en el mapa.</span>
</div>

<script>
const MENU = {{ menu | tojson }};
let map, marker, cur = {lat:null, lon:null}, selId=null;

function fmt(n){return (Math.round(n*100)/100).toFixed(2)}
function $id(x){return document.getElementById(x)}

function ensureMap(){
  if(map) return;
  map = L.map('map').setView([-12.0464, -77.0428], 13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(map);
  map.on('click', e=>{
    const la=+e.latlng.lat.toFixed(6), lo=+e.latlng.lng.toFixed(6);
    if(marker) map.removeLayer(marker);
    marker=L.marker([la,lo]).addTo(map);
    cur.lat=la; cur.lon=lo;
    $id('coords').innerText=`Coords: ${la}, ${lo}`;
  });
  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(p=>{
      map.setView([+p.coords.latitude.toFixed(6), +p.coords.longitude.toFixed(6)], 16);
    },()=>{}, {enableHighAccuracy:true, timeout:10000});
  }
}
ensureMap();

function menuUI(){
  const c=$id('menu'); c.innerHTML='';
  for(const [name, price] of Object.entries(MENU)){
    const row=document.createElement('div'); row.className='item';
    row.innerHTML = `<div>${name} <span class="badge">S/ ${price}</span></div>
      <input type="number" min="0" value="0" style="width:80px" data-name="${name}" />`;
    c.appendChild(row);
  }
  c.addEventListener('input', updateTotal);
}
menuUI();

function updateTotal(){
  let s=0;
  document.querySelectorAll('#menu input[type=number]').forEach(inp=>{
    const qty=parseInt(inp.value||'0',10), price=MENU[inp.dataset.name]||0;
    s += qty * price;
  });
  $id('total').innerText = fmt(s);
}

async function api(path, method='GET', body=null){
  const opt={ method, headers:{'Content-Type':'application/json'} };
  if(body) opt.body = JSON.stringify(body);
  const r = await fetch(path,opt); const j=await r.json();
  if(!r.ok){ alert(j.error||'Error'); throw new Error(j.error||'Error'); }
  return j;
}

async function createPin(){
  const phone=$id('phone').value.trim(), pin=$id('pin').value.trim();
  await api('/api/auth/pin','POST',{ phone, pin });
  alert('PIN creado');
}
async function verifyPin(){
  const phone=$id('phone').value.trim(), pin=$id('pin').value.trim();
  const r = await api('/api/auth/verify','POST',{ phone, pin });
  if(r.ok) location.reload();
}

async function loadAddresses(){
  const r = await fetch('/api/addresses'); if(r.status===401) return;
  const j = await r.json(); const box=$id('addrList'); box.innerHTML='';
  (j.list||[]).forEach(a=>{
    const li=document.createElement('div'); li.className='item';
    li.innerHTML = `
      <div><b>${a.alias || '(sin alias)'}</b> · ${a.address}<br><span class="badge">${a.lat}, ${a.lon}</span></div>
      <div style="display:flex;gap:6px">
        <button class="secondary" onclick="useAddress(${a.id}, '${(a.address||'').replace(/'/g,"\\'")}', ${a.lat}, ${a.lon})">Usar</button>
        <button class="secondary" onclick="editAddress(${a.id}, '${(a.alias||'').replace(/'/g,"\\'")}', '${(a.address||'').replace(/'/g,"\\'")}', ${a.lat}, ${a.lon})">Editar</button>
        <button onclick="delAddress(${a.id})">Eliminar</button>
      </div>`;
    box.appendChild(li);
  });
}
loadAddresses();

function useAddress(id, addr, la, lo){
  selId=id; $id('address').value=addr; cur.lat=la; cur.lon=lo;
  if(map){ map.setView([la,lo], 16); if(marker) map.removeLayer(marker); marker=L.marker([la,lo]).addTo(map); }
  $id('coords').innerText=`Coords: ${la}, ${lo}`;
}
function editAddress(id, alias, addr, la, lo){
  selId=id; $id('alias').value=alias; useAddress(id, addr, la, lo);
}
function clearSel(){ selId=null; $id('alias').value=''; }

async function saveAddress(){
  const alias=$id('alias').value.trim(), address=$id('address').value.trim();
  if(!address || cur.lat==null || cur.lon==null) return alert('Completa dirección y coordenadas');
  if(selId){ await api('/api/addresses','PUT',{ id:selId, alias, address, lat:cur.lat, lon:cur.lon }); }
  else     { await api('/api/addresses','POST',{ alias, address, lat:cur.lat, lon:cur.lon }); }
  selId=null; $id('alias').value=''; loadAddresses();
}

async function delAddress(id){
  await api('/api/addresses','DELETE',{ id });
  if(selId===id){ selId=null; $id('alias').value=''; }
  loadAddresses();
}

async function placeOrder(){
  const address=$id('address').value.trim();
  if(!address || cur.lat==null || cur.lon==null) return alert('Completa dirección y fija coordenadas');
  const items=[]; document.querySelectorAll('#menu input[type=number]').forEach(inp=>{
    const qty=parseInt(inp.value||'0',10); if(qty>0) items.push({ name: inp.dataset.name, qty, price: MENU[inp.dataset.name]||0 });
  });
  if(!items.length) return alert('Agrega al menos 1 ítem');
  const r = await api('/api/orders','POST',{ address, lat:cur.lat, lon:cur.lon, items });
  alert('Pedido creado – ID: '+r.order.id+' (S/ '+r.order.total+')');
  document.querySelectorAll('#menu input[type=number]').forEach(inp=> inp.value=0); updateTotal();
}
</script>
"""

REPARTIDOR_HTML = """
<div class="card">
  <h1>🚴 Repartidor – Toma pedidos</h1>
  <div class="row">
    <div><label>Tu teléfono</label><input id="dphone" placeholder="+51 999 999 999" /></div>
    <div style="display:flex;gap:8px;align-items:end">
      <button class="secondary" onclick="getLoc()">📍 Usar mi ubicación</button>
      <button onclick="saveLoc()">💾 Guardar ubicación</button>
    </div>
  </div>
  <div id="dmap" style="margin-top:8px"></div>
  <div class="badge" id="dcoords">Coords: — , —</div>
</div>

<div class="card">
  <h2>Pedidos nuevos</h2>
  <div class="list" id="olist"></div>
</div>

<script>
let dmap, dmarker, dcur={lat:null, lon:null};
function ensureDMap(){
  if(dmap) return;
  dmap = L.map('dmap').setView([-12.0464, -77.0428], 13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(dmap);
}
ensureDMap();

function getLoc(){
  if(!navigator.geolocation) return alert('Sin geolocalización');
  navigator.geolocation.getCurrentPosition(p=>{
    const la=+p.coords.latitude.toFixed(6), lo=+p.coords.longitude.toFixed(6);
    if(dmarker) dmap.removeLayer(dmarker);
    dmarker=L.marker([la,lo]).addTo(dmap);
    dmap.setView([la,lo], 16);
    dcur.lat=la; dcur.lon=lo; document.getElementById('dcoords').innerText=`Coords: ${la}, ${lo}`;
  }, e=>alert('Ubicación: '+e.message), {enableHighAccuracy:true});
}
async function api(path, method='GET', body=null){
  const opt = { method, headers:{'Content-Type':'application/json'} };
  if(body) opt.body = JSON.stringify(body);
  const r = await fetch(path, opt); const j = await r.json();
  if(!r.ok){ alert(j.error||'Error'); throw new Error(j.error||'Error'); }
  return j;
}
async function saveLoc(){
  const phone = document.getElementById('dphone').value.trim();
  if(!phone) return alert('Ingresa tu teléfono');
  await api('/api/drivers','PUT',{ phone, lat:dcur.lat, lon:dcur.lon });
  alert('Ubicación guardada');
}
async function loadOrders(){
  const j = await api('/api/orders','GET');
  const box = document.getElementById('olist'); box.innerHTML='';
  (j.orders||[]).forEach(o=>{
    const li=document.createElement('div'); li.className='item';
    li.innerHTML = `
      <div>
        <div><b>${o.address}</b></div>
        <div class="badge">S/ ${o.total} · ${new Date(o.created_at).toLocaleString()}</div>
      </div>
      <button onclick="takeOrder(${o.id})">Tomar</button>`;
    box.appendChild(li);
  });
}
async function takeOrder(id){
  const phone = document.getElementById('dphone').value.trim();
  if(!phone) return alert('Ingresa tu teléfono');
  const j = await api('/api/orders/'+id+'/assign','POST',{ driver_phone: phone });
  alert(j.ok ? ('Pedido tomado · ETA ~'+(j.eta_min ?? '?')+' min') : (j.error || 'Error'));
  loadOrders();
}
loadOrders(); setInterval(loadOrders, 5000);
</script>
"""

RESTAURANTE_HTML = """
<div class="card">
  <h1>🏪 Restaurante – Panel</h1>
  <p class="badge">Vista administrativa: pedidos y repartidores.</p>
</div>

<div class="card">
  <h2>Pedidos</h2>
  <table id="orders"><thead>
    <tr><th>ID</th><th>Estado</th><th>Dirección</th><th>Total</th><th>Driver</th><th>ETA</th><th>Creado</th><th>Acciones</th></tr>
  </thead><tbody></tbody></table>
</div>

<div class="card">
  <h2>Repartidores</h2>
  <table id="drivers"><thead>
    <tr><th>Teléfono</th><th>Lat</th><th>Lon</th><th>Status</th><th>Activos</th><th>Actualizado</th></tr>
  </thead><tbody></tbody></table>
</div>

<script>
async function api(path, method='GET', body=null){
  const opt={ method, headers:{'Content-Type':'application/json'} };
  if(body) opt.body = JSON.stringify(body);
  const r=await fetch(path,opt); const j=await r.json();
  if(!r.ok){ console.error(j); return { ok:false, error:j.error||'Error' }; }
  return j;
}
async function loadAdmin(){
  const o = await api('/api/orders/all'); const d = await api('/api/drivers');
  const ot = document.querySelector('#orders tbody'); ot.innerHTML='';
  (o.orders||[]).forEach(x=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `
      <td>${x.id}</td><td>${x.status}</td><td>${x.address}</td>
      <td>S/ ${x.total}</td><td>${x.assigned_driver||'—'}</td>
      <td>${x.eta_min ?? '—'}</td><td>${new Date(x.created_at).toLocaleString()}</td>
      <td>${x.status!=='delivered' ? `<button onclick="deliver(${x.id})">Entregado</button>` : '—'}</td>`;
    ot.appendChild(tr);
  });
  const dt = document.querySelector('#drivers tbody'); dt.innerHTML='';
  (d.list||[]).forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `<td>${r.phone}</td><td>${r.lat ?? '—'}</td><td>${r.lon ?? '—'}</td>
                    <td>${r.status}</td><td>${r.active_orders}</td><td>${new Date(r.updated_at).toLocaleString()}</td>`;
    dt.appendChild(tr);
  });
}
async function deliver(id){
  const r = await api('/api/orders/'+id+'/deliver','POST');
  if(r.ok) loadAdmin(); else alert(r.error||'Error');
}
loadAdmin(); setInterval(loadAdmin, 5000);
</script>
"""

# --------------------- Rutas UI ---------------------
@app.route("/")
def home():
    return redirect(url_for("cliente"))

@app.route("/cliente")
def cliente():
    return render_page(CLIENTE_HTML, title="Cliente", tab="c",
                       phone=session.get("phone",""), menu=MENU)

@app.route("/repartidor")
def repartidor():
    return render_page(REPARTIDOR_HTML, title="Repartidor", tab="r")

@app.route("/restaurante")
def restaurante():
    return render_page(RESTAURANTE_HTML, title="Restaurante", tab="a")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("cliente"))

# --------------------- API ---------------------
@app.post("/api/auth/pin")
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

@app.post("/api/auth/verify")
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

def require_session_json():
    cid = session.get("cid")
    return (cid, None) if cid else (None, (jsonify(error="No autorizado"), 401))

# Direcciones
@app.get("/api/addresses")
def api_addresses_get():
    cid, err = require_session_json()
    if err: return err
    rows = Address.query.filter_by(client_id=cid).order_by(Address.created_at.desc()).all()
    return jsonify(ok=True, list=[{
        "id":r.id, "alias":r.alias, "address":r.address,
        "lat":r.lat, "lon":r.lon, "is_default":r.is_default
    } for r in rows])

@app.post("/api/addresses")
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

@app.put("/api/addresses")
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

@app.delete("/api/addresses")
def api_addresses_delete():
    cid, err = require_session_json()
    if err: return err
    d = request.get_json(force=True)
    r = Address.query.filter_by(id=d.get("id"), client_id=cid).first()
    if not r: return jsonify(error="No encontrado"), 404
    db.session.delete(r); db.session.commit()
    return jsonify(ok=True)

# Pedidos
@app.get("/api/orders")
def api_orders_new():
    rows = Order.query.filter_by(status="new").order_by(Order.created_at.desc()).all()
    return jsonify(ok=True, orders=[{
        "id":o.id, "address":o.address, "total":o.total,
        "lat":o.lat, "lon":o.lon, "created_at":o.created_at.isoformat()
    } for o in rows])

@app.get("/api/orders/all")
def api_orders_all():
    rows = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify(ok=True, orders=[{
        "id":o.id, "status":o.status, "address":o.address, "total":o.total,
        "assigned_driver":o.assigned_driver, "eta_min":o.eta_min,
        "created_at":o.created_at.isoformat()
    } for o in rows])

@app.post("/api/orders")
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

@app.post("/api/orders/<int:order_id>/assign")
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
        eta = int(round((dist/25.0)*60))  # 25 km/h
    o.status = "assigned"; o.assigned_driver = driver_phone; o.eta_min = eta
    drv.active_orders = (drv.active_orders or 0) + 1
    drv.status = "busy"
    db.session.commit()
    return jsonify(ok=True, order_id=o.id, eta_min=eta)

@app.post("/api/orders/<int:order_id>/deliver")
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

# Repartidores
@app.get("/api/drivers")
def api_drivers_get():
    rows = Driver.query.order_by(Driver.updated_at.desc()).all()
    return jsonify(ok=True, list=[{
        "phone":r.phone, "lat":r.lat, "lon":r.lon, "status":r.status,
        "active_orders":r.active_orders, "updated_at": (r.updated_at or datetime.utcnow()).isoformat()
    } for r in rows])

@app.put("/api/drivers")
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

# --------------------- Misc ---------------------
@app.route("/ping")
def ping(): return "pong"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
