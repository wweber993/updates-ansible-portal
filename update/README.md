# 📘 API de Updates

Esta API registra **status de atualizações de servidores Windows e Linux**, armazenando os dados em arquivos JSON locais em `/opt/update-web/static-web/static/json`.

Cada servidor pertence a **um único ambiente**.  
O campo `server_received_at` é gerado automaticamente com timezone **UTC-3 (Brasília)**.  

---

## 🧭 Como funciona

1. O cliente envia um `POST` com os detalhes do update.  
2. O servidor grava ou atualiza o histórico em `/opt/update-web/static/json/{server_name}.json`.  
3. A resposta retorna o total de registros no histórico do servidor.  

---

## 📂 Endpoints disponíveis

### 🪟 Windows Updates
`POST /api/v1/windows/update`

📌 **Campos obrigatórios**
- `server_name` (string) – Nome do servidor
- `ip_address` (string) – IP do servidor
- `update_status` (enum: `SUCCESS`, `FAILED`, `NO_UPDATES_FOUND`)
- `report_timestamp` (string, formato ISO ex: `2025-09-16T12:00:00Z`)
- `ambiente` (string) – Ambiente lógico do servidor

📌 **Campos opcionais**
- `installed_kbs` (array de strings, ex: `["KB5005565", "KB5013942"]`)
- `error_details` (string)

---

### 🐧 Linux Updates
`POST /api/v1/linux/update`

📌 **Campos obrigatórios**
- `server_name` (string)
- `ip_address` (string)
- `update_status` (enum: `SUCCESS`, `FAILED`, `NO_UPDATES_FOUND`)
- `report_timestamp` (string)
- `ambiente` (string)

📌 **Campos opcionais**
- `installed_packages` (array de strings, ex: `["nginx-1.18.0", "openssl-1.1.1k"]`)
- `error_details` (string)

---

## 📝 Exemplos de payloads

### Windows
{
  "server_name": "win-001",
  "ip_address": "10.1.2.3",
  "update_status": "SUCCESS",
  "report_timestamp": "2025-09-16T12:00:00Z",
  "ambiente": "prod",
  "installed_kbs": ["KB5005565", "KB5013942"]
}

### Linux
{
  "server_name": "lin-101",
  "ip_address": "10.1.2.4",
  "update_status": "FAILED",
  "report_timestamp": "2025-09-16T12:30:00Z",
  "ambiente": "dev",
  "installed_packages": ["nginx-1.18.0"],
  "error_details": "Falha ao baixar pacote"
}

## 📊 Respostas

### Sucesso

{
  "message": "Update Linux recebido com sucesso.",
  "history_count": 5
}

### Erro

{
  "error": "Campo obrigatório ausente: ambiente"
}
