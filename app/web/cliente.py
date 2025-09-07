from flask import Blueprint, session
from ..base import render_page
from ..utils import MENU

cliente_bp = Blueprint("cliente", __name__)

CLIENTE_HTML = """<div class="card">
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
window.addEventListener('DOMContentLoaded', function(){
  const MENU = {{ menu | tojson }};
  let map, marker, cur = {lat:null, lon:null}, selId=null;

  function fmt(n){return (Math.round(n*100)/100).toFixed(2)}
  function $id(x){return document.getElementById(x)}

  function ensureMap(){
    if(map) return;
    if(!window.L){ setTimeout(ensureMap, 100); return; }
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
    c.addEventListener('input', ()=>{
      let s=0;
      document.querySelectorAll('#menu input[type=number]').forEach(inp=>{
        const qty=parseInt(inp.value||'0',10), price=MENU[inp.dataset.name]||0;
        s += qty * price;
      });
      $id('total').innerText = fmt(s);
    });
  }
  menuUI();

  async function api(path, method='GET', body=null){
    const opt={ method, headers:{'Content-Type':'application/json'} };
    if(body) opt.body = JSON.stringify(body);
    const r = await fetch(path,opt); const j=await r.json();
    if(!r.ok){ alert(j.error||'Error'); throw new Error(j.error||'Error'); }
    return j;
  }

  window.createPin = async function(){
    const phone=$id('phone').value.trim(), pin=$id('pin').value.trim();
    await api('/api/auth/pin','POST',{ phone, pin });
    alert('PIN creado');
  }
  window.verifyPin = async function(){
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

  window.useAddress = function(id, addr, la, lo){
    selId=id; $id('address').value=addr; cur.lat=la; cur.lon=lo;
    if(map){ map.setView([la,lo], 16); if(marker) map.removeLayer(marker); marker=L.marker([la,lo]).addTo(map); }
    $id('coords').innerText=`Coords: ${la}, ${lo}`;
  }
  window.editAddress = function(id, alias, addr, la, lo){
    selId=id; $id('alias').value=alias; window.useAddress(id, addr, la, lo);
  }
  window.clearSel = function(){ selId=null; $id('alias').value=''; }

  window.saveAddress = async function(){
    const alias=$id('alias').value.trim(), address=$id('address').value.trim();
    if(!address || cur.lat==null || cur.lon==null) return alert('Completa dirección y coordenadas');
    if(selId){ await api('/api/addresses','PUT',{ id:selId, alias, address, lat:cur.lat, lon:cur.lon }); }
    else     { await api('/api/addresses','POST',{ alias, address, lat:cur.lat, lon:cur.lon }); }
    selId=null; $id('alias').value=''; loadAddresses();
  }

  window.delAddress = async function(id){
    await api('/api/addresses','DELETE',{ id });
    if(selId===id){ selId=null; $id('alias').value=''; }
    loadAddresses();
  }

  window.placeOrder = async function(){
    const address=$id('address').value.trim();
    if(!address || cur.lat==null || cur.lon==null) return alert('Completa dirección y fija coordenadas');
    const items=[]; document.querySelectorAll('#menu input[type=number]').forEach(inp=>{
      const qty=parseInt(inp.value||'0',10); if(qty>0) items.push({ name: inp.dataset.name, qty, price: MENU[inp.dataset.name]||0 });
    });
    if(!items.length) return alert('Agrega al menos 1 ítem');
    const r = await api('/api/orders','POST',{ address, lat:cur.lat, lon:cur.lon, items });
    alert('Pedido creado – ID: '+r.order.id+' (S/ '+r.order.total+')');
    document.querySelectorAll('#menu input[type=number]').forEach(inp=> inp.value=0);
    document.getElementById('total').innerText='0.00';
  }
});
</script>
