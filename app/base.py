from flask import render_template_string

BASE_SHELL = """<!doctype html>
<html lang="es"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{{ title }}</title>
<link rel="stylesheet" href="https://unpkg.com/modern-css-reset/dist/reset.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<style>
 body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;background:#f4f6fb;color:#0f172a}
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
    <a href="{{ url_for('cliente.cliente') }}" class="{{ 'active' if tab=='c' else '' }}">Cliente</a>
    <a href="{{ url_for('repartidor.repartidor') }}" class="{{ 'active' if tab=='r' else '' }}">Repartidor</a>
    <a href="{{ url_for('restaurante.restaurante') }}" class="{{ 'active' if tab=='a' else '' }}">Restaurante</a>
    {% if session.get('cid') %} <a href="{{ url_for('cliente.logout') }}">Cerrar sesión</a> {% endif %}
  </nav>
  {{ content|safe }}
</div>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js" defer></script>
</body></html>
"""

def render_page(content_html: str, **ctx):
    inner = render_template_string(content_html, **ctx)
    return render_template_string(BASE_SHELL, content=inner, **ctx)
