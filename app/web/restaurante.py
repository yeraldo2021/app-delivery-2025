from flask import Blueprint
from ..base import render_page

restaurante_bp = Blueprint("restaurante", __name__)

RESTAURANTE_HTML = """<div class="card">
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
window.addEventListener('DOMContentLoaded', function(){
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
  window.deliver = async function(id){
    const r = await api('/api/orders/'+id+'/deliver','POST');
    if(r.ok) loadAdmin(); else alert(r.error||'Error');
  }
  loadAdmin(); setInterval(loadAdmin, 5000);
});
</script>
