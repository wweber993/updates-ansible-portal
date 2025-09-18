from flask import Flask, request, jsonify, abort, Response
import os, json, re
from datetime import datetime, timezone, timedelta
import markdown

DATA_DIR = "/opt/update-web/static/json"
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)

# Timezone Brasil (UTC-3)
BRASIL_TZ = timezone(timedelta(hours=-3))

# -------------------------------
# Funções utilitárias
# -------------------------------
def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)

def server_history_path(server_name: str) -> str:
    safe = sanitize_filename(server_name)
    return os.path.join(DATA_DIR, f"{safe}.json")

def load_history(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def atomic_write_json(path: str, content: list) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# -------------------------------
# Renderização do README.md em HTML estilizado
# -------------------------------
def read_readme_html():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
        return f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>📘 Documentação API Updates</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background: #f9f9f9;
                    margin: 0;
                    padding: 2rem;
                }}
                .container {{
                    max-width: 1000px;
                    margin: auto;
                    background: #fff;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{
                    border-bottom: 2px solid #eaecef;
                    padding-bottom: .3em;
                }}
                pre, code {{
                    background: #f6f8fa;
                    padding: .5rem;
                    border-radius: 6px;
                    font-family: monospace;
                }}
                pre {{
                    overflow-x: auto;
                }}
                table {{
                    border-collapse: collapse;
                    margin: 1rem 0;
                    width: 100%;
                }}
                table, th, td {{
                    border: 1px solid #dfe2e5;
                }}
                th, td {{
                    padding: 0.6rem;
                    text-align: left;
                }}
                th {{
                    background: #f3f4f6;
                }}
                .endpoint {{
                    border-left: 6px solid #007bff;
                    padding: 1rem;
                    margin: 1rem 0;
                    background: #fefefe;
                    border-radius: 6px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
                .endpoint h3 {{
                    margin-top: 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {html_content}
            </div>
        </body>
        </html>
        """
    return "<h1>📄 Documentação não encontrada</h1>"

@app.route("/")
def docs():
    return Response(read_readme_html(), mimetype="text/html")

# -------------------------------
# API WINDOWS
# -------------------------------
@app.route("/api/v1/windows/update", methods=["POST"])
def ingest_windows_update():
    data = request.get_json(force=True)
    required_fields = ["server_name", "ip_address", "update_status", "report_timestamp", "ambiente"]
    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"Campo obrigatório ausente: {field}")

    path = server_history_path(data["server_name"])
    history = load_history(path)

    entry = {
        "server_name": data["server_name"],
        "ip_address": data["ip_address"],
        "update_status": data["update_status"],
        "installed_kbs": data.get("installed_kbs", []),
        "error_details": data.get("error_details"),
        "report_timestamp": data["report_timestamp"],
        "server_received_at": datetime.now(BRASIL_TZ).isoformat(),
        "ambiente": data["ambiente"],
        "so": "Windows"
    }

    history.append(entry)
    atomic_write_json(path, history)

    return jsonify({"message": "Update Windows recebido com sucesso.", "history_count": len(history)}), 201

# -------------------------------
# API LINUX
# -------------------------------
@app.route("/api/v1/linux/update", methods=["POST"])
def ingest_linux_update():
    data = request.get_json(force=True)
    required_fields = ["server_name", "ip_address", "update_status", "report_timestamp", "ambiente"]
    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"Campo obrigatório ausente: {field}")

    path = server_history_path(data["server_name"])
    history = load_history(path)

    entry = {
        "server_name": data["server_name"],
        "ip_address": data["ip_address"],
        "update_status": data["update_status"],
        "installed_packages": data.get("installed_packages", []),
        "error_details": data.get("error_details"),
        "report_timestamp": data["report_timestamp"],
        "server_received_at": datetime.now(BRASIL_TZ).isoformat(),
        "ambiente": data["ambiente"],
        "so": "Linux"
    }

    history.append(entry)
    atomic_write_json(path, history)

    return jsonify({"message": "Update Linux recebido com sucesso.", "history_count": len(history)}), 201

# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
