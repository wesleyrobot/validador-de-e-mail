# 📧 Sistema de Validação de E-mails e Gestão de Contatos

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Sistema completo de validação de e-mails, processamento inteligente de contatos e exportação de dados com interface web moderna.

![Sistema de Validação](https://img.shields.io/badge/Downloads-XLSX%20%7C%20CSV-green)

---

## 🚀 Funcionalidades

### ✅ Validação de E-mails
- Validação de sintaxe (formato correto)
- Verificação DNS/MX (domínio existe)
- Detecção de e-mails temporários/descartáveis
- Categorização automática (válido, inválido, syntax_only)

### 📊 Processamento Inteligente
- Leitura automática de múltiplos formatos (CSV, XLSX, XLS)
- Detecção inteligente de colunas (nome, e-mail, telefone, empresa)
- Processamento assíncrono em background
- Suporte para arquivos grandes (até 100MB)

### 📥 Exportação Flexível
- Download completo (todos os dados processados)
- Download filtrado (apenas nome + e-mail válidos)
- Formatos: XLSX e CSV
- Encoding UTF-8 com BOM para Excel

### 🎨 Interface Web
- Interface moderna e responsiva (Streamlit)
- Upload de arquivos via drag & drop
- Visualização em tempo real do progresso
- Tabela interativa com dados processados
- Botões de download direto

---

## 🏗️ Arquitetura
┌─────────────────┐
│   Streamlit     │  Interface Web (Porta 8501)
│   Frontend      │
└────────┬────────┘
│
┌────▼────┐
│  Nginx  │  Proxy Reverso (Porta 80)
└────┬────┘
│
┌────▼────────────────┐
│   FastAPI Backend   │  API REST (Porta 8000)
│                     │
│  • Upload           │
│  • Processamento    │
│  • Validação DNS    │
│  • Download         │
└─────────────────────┘

---

## 🛠️ Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **Pandas** - Manipulação de dados
- **OpenPyXL** - Leitura/escrita de arquivos Excel
- **dnspython** - Validação DNS de e-mails
- **Celery** - Processamento assíncrono

### Frontend
- **Streamlit** - Interface web interativa
- **Plotly** - Gráficos e visualizações

### Infraestrutura
- **Nginx** - Proxy reverso e load balancer
- **Uvicorn** - Servidor ASGI de alta performance
- **Python 3.10+**

---

## 📦 Instalação

### Pré-requisitos
```bash
Python 3.10+
pip
virtualenv
nginx (opcional, para produção)
Setup

Clone o repositório:

bashgit clone https://github.com/wesleyrobot/validador-de-e-mail.git
cd validador-de-e-mail

Crie ambiente virtual:

bashpython3 -m venv venv
source venv/bin/activate  # Linux/Mac

Instale dependências:

bashpip install -r requirements.txt

Configure variáveis de ambiente:

bashcp .env.example .env
# Edite .env conforme necessário

Inicie os serviços:

API:
bashuvicorn contact_api:app --host 0.0.0.0 --port 8000 --reload
Frontend:
bashstreamlit run streamlit_app.py --server.port 8501

Acesse:


Frontend: http://localhost:8501
API Docs: http://localhost:8000/docs


📡 API Endpoints
Upload
httpPOST /upload
Content-Type: multipart/form-data

Parâmetros:
- file: arquivo (CSV, XLSX, XLS)

Resposta:
{
  "job_id": "uuid",
  "status": "processing",
  "total_contacts": 1000
}
Status do Job
httpGET /jobs/{job_id}

Resposta:
{
  "job_id": "uuid",
  "status": "done",
  "progress": 100
}
Download Completo
httpGET /api/download/{job_id}?format=xlsx

Parâmetros:
- format: xlsx | csv
Download Filtrado
httpGET /api/download/{job_id}/filtered?format=xlsx&valid_only=true

Parâmetros:
- format: xlsx | csv
- valid_only: true | false

🔧 Configuração Nginx (Exemplo)
nginxupstream validador_api {
    server 127.0.0.1:8000;
}

upstream validador_frontend {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name seu-dominio.com;
    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://validador_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://validador_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

📊 Performance

✅ Validação: ~1000 e-mails/minuto
📁 Arquivo Máximo: 100MB
🔄 Processamento: Assíncrono
💾 Formatos: CSV, XLSX, XLS
📤 Exportação: XLSX, CSV


🔐 Segurança

✅ Validação de tipos de arquivo
✅ Limite de tamanho de upload
✅ Sanitização de dados
✅ CORS configurado
⚠️ Use variáveis de ambiente (.env)
⚠️ Nunca commite senhas ou tokens


📈 Roadmap

 Validação SMTP completa
 Dashboard analytics
 Webhook notifications
 Integração com CRM
 API de deduplicação
 Suporte multi-idioma


📝 Changelog
v1.0.0 (2025-10-13)

✅ Sistema funcional completo
✅ Validação DNS de e-mails
✅ Interface Streamlit
✅ API FastAPI
✅ Download XLSX/CSV
✅ Processamento assíncrono


📄 Licença
MIT License - Veja LICENSE

👨‍💻 Autor
Wesley Robot

GitHub: @wesleyrobot


<div align="center">
⭐ Se este projeto foi útil, considere dar uma estrela!
Made with ❤️ by Wesley Robot
</div>
