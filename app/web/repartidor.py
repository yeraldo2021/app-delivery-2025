from flask import Blueprint
from ..base import render_page

repartidor_bp = Blueprint("repartidor", __name__)

REPARTIDOR_HTML = """<div class="card">
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
window.addEventListener('DOMContentLoaded', function(){
  let dmap, dmarker, dcur={lat:null, lon:null};

  function ensureDMap(){
    if(dmap) return;
    if(!window.L){ setTimeout(ensureDMap, 100); return; }
    dmap = L.map('dmap').setView([-12.0464, -77.0428], 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(dmap);
  }
  ensureDMap();

  window.getLoc = function(){
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

  window.saveLoc = async function(){
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
  window.takeOrder = async function(id){
    const phone = document.getElementById('dphone').value.trim();
    if(!phone) return alert('Ingresa tu teléfono');
    const j = await api('/api/orders/'+id+'/assign','POST',{ driver_phone: phone });
    alert(j.ok ? ('Pedido tomado · ETA ~'+(j.eta_min ?? '?')+' min') : (j.error || 'Error'));
    loadOrders();
  }

  loadOrders(); setInterval(loadOrders, 5000);
});
</script>
