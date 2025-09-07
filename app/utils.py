import math, hashlib

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
    R=6371.0
    import math as _m
    p1=_m.radians(lat1); p2=_m.radians(lat2)
    dphi=_m.radians(lat2-lat1); dl=_m.radians(lon2-lon1)
    a=_m.sin(dphi/2)**2+_m.cos(p1)*_m.cos(p2)*_m.sin(dl/2)**2
    return 2*R*_m.asin(min(1, _m.sqrt(a)))
