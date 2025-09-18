from flask import Flask, jsonify, send_from_directory, render_template
from datetime import datetime, timedelta
import os, json, threading, glob

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(APP_ROOT, "static", "json")

app = Flask(__name__, template_folder="templates", static_folder="static")

# Cache simples em memória
_cache_lock = threading.Lock()
_cache_data = None
_cache_expire_at = None
_CACHE_TTL = 60  # segundos

def _safe_listdir_json():
    if not os.path.isdir(JSON_DIR):
        return []
    return glob.glob(os.path.join(JSON_DIR, "*.json"))

def _load_all_json():
    merged = []
    for path in _safe_listdir_json():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged.extend(data)
                elif isinstance(data, dict):
                    merged.append(data)
        except Exception:
            # ignora arquivos inválidos sem derrubar o endpoint
            continue

    # Normalização mínima de campos esperados (sem inventar info)
    for item in merged:
        item.setdefault("server_name", None)
        item.setdefault("ip_address", None)
        item.setdefault("ambiente", None)

        # Normaliza SO
        so = item.get("so")
        if isinstance(so, str):
            so_clean = so.strip().capitalize()
            if so_clean.lower().startswith("win"):
                item["so"] = "Windows"
            elif so_clean.lower().startswith("lin"):
                item["so"] = "Linux"
            else:
                item["so"] = so_clean

        # Normaliza status
        status = item.get("update_status")
        if isinstance(status, str):
            status_clean = status.strip().upper()
            if status_clean in {"SUCCESS", "FAILED", "NO_UPDATES_FOUND"}:
                item["update_status"] = status_clean
            else:
                item["update_status"] = status_clean or None
        else:
            item["update_status"] = None

        item.setdefault("report_timestamp", None)
        item.setdefault("installed_kbs", None)       # Windows
        item.setdefault("installed_packages", None)  # Linux
        item.setdefault("error_details", None)

    return merged

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/all-data")
def all_data():
    global _cache_data, _cache_expire_at
    now = datetime.utcnow()
    with _cache_lock:
        if _cache_data is None or _cache_expire_at is None or now >= _cache_expire_at:
            data = _load_all_json()
            _cache_data = {"count": len(data), "items": data, "generated_at": now.isoformat() + "Z"}
            _cache_expire_at = now + timedelta(seconds=_CACHE_TTL)
        return jsonify(_cache_data)

# rota opcional para servir páginas diretamente (útil em debug local)
@app.route("/pages/<path:filename>")
def pages(filename):
    return send_from_directory(os.path.join(app.static_folder, "pages"), filename)

if __name__ == "__main__":
    # Porta padrão 8000 (ajuste se necessário)
    app.run(host="0.0.0.0", port=8080)
