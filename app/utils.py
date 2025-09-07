import math, hashlib

MENU = {
    "Chaufa": 18.0,
    "Tallarín saltado": 20.0,
    "Wantán frito (10u)": 12.0,
    "Pollo a la brasa (1/4)": 19.0,
    "Inka Kola 500ml": 5.0,
}

def sanitize_phone(s: str) -> str:
    if not s:
        return ""
    # Mantén +, dígitos; normaliza a E.164 Perú si no trae +51
    t = "".join(ch for ch in s if ch.isdigit() or ch == "+")
    if t.startswith("+"):
        return t
    d = "".join(ch for ch in t if ch.isdigit())
    return "+51" + d if d else ""

def looks_valid_phone(ph: str) -> bool:
    if not ph:
        return False
    # Acepta +51XXXXXXXXX (11 dígitos contando 51) o 9 dígitos locales
    d = "".join(ch for ch in ph if ch.isdigit())
    if ph.startswith("+51") or d.startswith("51"):
        return len(d) == 11
    return len(d) == 9

def hash_pin(e164: str, pin4: str) -> str:
    return hashlib.sha256((e164 + ":" + pin4).encode()).hexdigest()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))
