# Portal de Atualizações (Ansible/AWX + Flask)

Sistema gratuito e simples para **instalar atualizações** (Windows e Linux) com Ansible/AWX e **acompanhar os resultados** em um **portal web** leve. Sem precisar de softwares pagos: a API recebe os resultados dos playbooks e grava **JSONs** que o portal lê para montar gráficos e relatórios.

> **Arquitetura resumida**
>
> - **Playbooks (AWX/Ansible)** executam updates nos servidores e fazem POST no endpoint da **API**.
> - **API (Flask)** valida os dados e grava/atualiza arquivos JSON (1 arquivo por servidor).
> - **Portal Web (Flask + Tailwind + Chart.js)** lê os JSONs e exibe **dashboards**, filtros por **ambiente**, **SO** e **período**, além de páginas de histórico e falhas.

---

## 🛑 ALERTA/AVISO
![Requer AWX](https://img.shields.io/badge/Requer-AWX%20Tower-red?style=for-the-badge&logo=ansible)
> 🛑 **Importante:** Este projeto depende do **AWX** para orquestrar a execução dos playbooks de atualização.

## 🗂 Estrutura do repositório

```
📁 playbooks/
   📄 update_linux.yml
   📄 update_windows.yml
📁 update/            ← API que recebe resultados e grava JSONs
   📄 app.py
   📄 requirements.txt
📁 update-web/        ← Portal web (Flask + Tailwind + Chart.js)
   📁 static/
      📁 js/
         📄 app.js
      📁 json/        ← pasta onde os JSONs ficam disponíveis ao portal
      📁 pages/
         📄 *.html    ← páginas do dashboard
   📁 templates/
      📄 index.html
   📄 app.py
   📄 requirements.txt

```

---

## 🚀 Componentes

### 1) API (porta 8000)
- Código: `update/app.py`
- Grava JSONs em **`/opt/update-web/static/json`** (por padrão no código atual).
- Endpoints principais:
  - `POST /api/v1/windows/update`
  - `POST /api/v1/linux/update`
- Timezone: grava `server_received_at` em **UTC-3 (Brasil)**.

**Formato de envio (exemplo Windows)**

```json
{
  "server_name": "HOWSUS01SEN",
  "ip_address": "10.151.200.3",
  "update_status": "SUCCESS",  // SUCCESS | FAILED | NO_UPDATES_FOUND
  "installed_kbs": ["KB5034441","KB5035853"],
  "error_details": null,
  "report_timestamp": "2025-09-16T12:00:00Z",
  "ambiente": "PRODUCAO"
}
```

**Exemplo de `curl`**

```bash
curl -X POST http://SEU_HOST:8000/api/v1/windows/update \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### 2) Portal Web (porta 8080)
- Código: `update-web/app.py`
- Lê os JSONs da pasta `update-web/static/json` e expõe dados em `/all-data` (usado pelo `static/js/app.js`).  
- Páginas principais (em `update-web/static/pages/`): **dashboard**, **falhas**, **por ambiente**, **por SO**, **por período**, **histórico**, **checa janela**, **reports**.

> **Importante:** No código atual da API, o diretório de saída está **hardcoded** como `/opt/update-web/static/json`. 

---

## 🛠️ Como rodar (dev)

# Update e Upgrade
```bash
sudo apt update && sudo apt upgrade -y
```

# Python e venv
```bash
sudo apt install -y python3 python3-venv python3-pip
```

# Dependências extras para pacotes Python que precisam compilar código nativo
```bash
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev \
                   libxml2-dev libxslt1-dev zlib1g-dev \
                   default-libmysqlclient-dev pkg-config
```

### API (porta 8000)
```bash
cd update
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py  # sobe em 0.0.0.0:8000
```

Acesse: `http://localhost:8000`

### Portal (porta 8080)
```bash
cd update-web
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py  # sobe em 0.0.0.0:8080
```

Acesse: `http://localhost:8080`

---

## 🧪 Teste rápido
Com os serviços rodando e a pasta de JSONs ajustada, envie um exemplo:

```bash
cat > sample.json <<'JSON'
{
  "server_name": "vm-sample-01",
  "ip_address": "192.168.1.10",
  "update_status": "SUCCESS",
  "installed_kbs": ["KB5034441"],
  "error_details": null,
  "report_timestamp": "2025-09-18T12:00:00Z",
  "ambiente": "LAB",
  "so": "Windows"
}
JSON

curl -X POST http://localhost:8000/api/v1/windows/update \
  -H "Content-Type: application/json" \
  -d @sample.json
```

Abra o portal e confira se o host aparece nos gráficos e nas listagens.

---

## 📦 AWX / Ansible

### Windows (`playbooks/update_windows.yml`)
- Instala **SecurityUpdates** e **CriticalUpdates**.
- Envia resultado para a API:
  - `api_endpoint: "http://ip-ou-dns:8000/api/v1/windows/update"`
  - `ambiente: "{ awx_inventory_name }"`  ← **o nome do inventário do AWX vira o ambiente**.

### Linux (`playbooks/update_linux.yml`)
- Detecta gerenciador de pacotes (**APT** ou **YUM/DNF**) e executa atualização segura.
- Envia resultado para a API:
  - `api_url: "http://ip-ou-dns:8000/api/v1/linux/update"`
  - `ambiente: "{ awx_inventory_name }"` ← **o nome do inventário do AWX vira o ambiente**.

> **Dicas no AWX/Tower**
>
> - Use `strategy: free` para grandes quantidades de hosts.
> - Defina credenciais e privilégios mínimos.
> - Nomeie os inventários **exatamente** como os ambientes (ex.: `PRODUCAO`, `HOMOLOG`, `LAB`).

---

## 🧩 Estrutura dos JSONs
A API mantém **1 arquivo por servidor**, contendo um **array** de eventos. Exemplo (arquivo `vm-sample-01.json`):

```json
[
  {
    "server_name": "vm-sample-01",
    "ip_address": "192.168.1.10",
    "update_status": "SUCCESS",
    "installed_kbs": ["KB5034441"],
    "error_details": null,
    "report_timestamp": "2025-09-18T12:00:00Z",
    "server_received_at": "2025-09-18T09:10:15-03:00",
    "ambiente": "LAB",
    "so": "Windows"
  }
]
```

O Portal consolida todos os arquivos de `static/json` e gera os gráficos com filtros.

---

## 🔒 Produção (sugestão)

- Coloque **Nginx** na frente das duas apps (API 8000 e Portal 8080), com HTTPS (Let's Encrypt).
- Restrinja a API por IP e/ou implemente **token por header** (ex.: `X-API-KEY`) — o código atual **não** tem autenticação.
- Configure **systemd** para subir os serviços no boot. Exemplos:

**`/etc/systemd/system/update-api.service`**
```ini
[Unit]
Description=API Updates (Flask)
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/sistema/update
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/sistema/update/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/portal-updates.service`**
```ini
[Unit]
Description=Portal Updates (Flask)
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/sistema/update-web
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/sistema/update-web/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---
