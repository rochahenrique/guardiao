# 🚀 Agente de Inovação TOTVS

Agente conversacional para coleta de ideias de inovação e oportunidades de processos do RH TOTVS.

## 📋 Visão Geral

Este projeto substitui o formulário Google Forms por um agente de IA que coleta respostas de forma conversacional e amigável, salvando os dados em uma planilha do Google Sheets.

### Tecnologias

- **Backend:** Python 3.11 + FastAPI
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **IA:** Proxy DTA TOTVS (compatível com OpenAI)
- **Deploy:** Docker + Google Cloud Run

## 🏗️ Estrutura do Projeto

```
agente-inovacao/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── requirements.txt     # Dependências Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Componente principal
│   │   ├── api.ts           # Serviço de API
│   │   ├── types.ts         # Tipos TypeScript
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Estilos globais
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml       # Para rodar local
├── .env.example             # Variáveis de ambiente
└── README.md
```

## 🚀 Como Rodar Localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- Ou: Node.js 18+ e Python 3.11+

### Opção 1: Docker Compose (Recomendado)

```bash
# 1. Clone ou extraia o projeto
cd agente-inovacao

# 2. Copie o arquivo de ambiente
cp .env.example .env

# 3. Edite o .env com suas configurações (opcional)
nano .env

# 4. Suba os containers
docker-compose up --build

# 5. Acesse
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Opção 2: Sem Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## ☁️ Deploy no Google Cloud Run

### 1. Configurar GCP

```bash
# Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Autenticar
gcloud auth login

# Selecionar projeto
gcloud config set project SEU_PROJETO_ID

# Habilitar APIs necessárias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Criar Secrets (Secret Manager)

```bash
# API Key do DTA
echo -n "sk-Q2m_kNH3orWeZX611razEQ" | \
  gcloud secrets create dta-api-key --data-file=-

# (Opcional) Google Sheets Credentials
gcloud secrets create google-sheets-creds \
  --data-file=./credentials.json
```

### 3. Deploy do Backend

```bash
cd backend

# Build e push da imagem
gcloud builds submit --tag gcr.io/SEU_PROJETO/agente-inovacao-backend

# Deploy no Cloud Run
gcloud run deploy agente-inovacao-backend \
  --image gcr.io/SEU_PROJETO/agente-inovacao-backend \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-secrets=DTA_API_KEY=dta-api-key:latest \
  --set-env-vars="DTA_PROXY_URL=https://proxy.dta.totvs.ai"
```

### 4. Deploy do Frontend

```bash
cd frontend

# Pegar URL do backend
BACKEND_URL=$(gcloud run services describe agente-inovacao-backend \
  --platform managed \
  --region southamerica-east1 \
  --format 'value(status.url)')

# Build e push
gcloud builds submit \
  --tag gcr.io/SEU_PROJETO/agente-inovacao-frontend \
  --build-arg VITE_API_URL=$BACKEND_URL

# Deploy
gcloud run deploy agente-inovacao-frontend \
  --image gcr.io/SEU_PROJETO/agente-inovacao-frontend \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated
```

## 📊 Configurar Google Sheets (Opcional)

### 1. Criar Service Account

1. Vá para [Google Cloud Console](https://console.cloud.google.com)
2. IAM & Admin → Service Accounts → Create
3. Dê um nome (ex: `agente-inovacao`)
4. Baixe a chave JSON

### 2. Criar Planilha

1. Crie uma planilha no Google Sheets
2. Compartilhe com o email da Service Account (Editor)
3. Copie o ID da planilha (da URL)

### 3. Configurar Headers

Na primeira linha da planilha, adicione:

| A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Data/Hora | Email | Processo | Resumo da Dor | Criticidade | Descrição Impacto | Pessoas Impactadas | Outros Ganhos | Impacta Outros | Horas Economizadas | Tipo Impacto | Envolvimento Áreas | Elementos Envolvidos | Solução Pensada |

### 4. Configurar Variáveis

```bash
# No .env ou Cloud Run
GOOGLE_SHEETS_ENABLED=true
SPREADSHEET_ID=seu_id_da_planilha
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

## 🔐 Controle de Acesso por Email

Para liberar apenas emails específicos:

```bash
# No .env ou Cloud Run
VALIDAR_EMAIL=true
EMAILS_AUTORIZADOS=joao.silva@totvs.com.br,maria.santos@totvs.com.br
```

Ou deixe vazio para aceitar qualquer @totvs.com.br:

```bash
VALIDAR_EMAIL=true
EMAILS_AUTORIZADOS=
```

## 📝 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Health check |
| GET | `/health` | Status da API |
| GET | `/perguntas` | Lista todas as perguntas |
| POST | `/validar-email` | Valida email autorizado |
| POST | `/iniciar` | Inicia nova sessão |
| POST | `/responder` | Envia resposta |
| GET | `/sessao/{id}` | Estado da sessão |

## 🎨 Customização

### Alterar Perguntas

Edite a lista `PERGUNTAS` em `backend/main.py`:

```python
PERGUNTAS = [
    {
        "id": "identificador_unico",
        "secao": 1,
        "titulo": "Título da Seção",
        "pergunta": "Texto da pergunta?",
        "tipo": "texto_curto",  # ou: texto_longo, email, multipla_escolha, checkbox
        "opcoes": ["Opção 1", "Opção 2"],  # se aplicável
        "obrigatoria": True
    },
    # ...
]
```

### Alterar Aparência

Edite as cores em `frontend/tailwind.config.js`:

```javascript
colors: {
  totvs: {
    primary: '#00A1E0',    // Azul principal
    secondary: '#003D73',  // Azul escuro
    accent: '#00D4AA',     // Verde água
  }
}
```

## 🐛 Troubleshooting

### Erro de CORS
Verifique se o backend está permitindo a origem do frontend.

### Erro ao conectar com proxy DTA
Verifique se a API key está correta e se a rede permite acesso ao proxy.

### Erro no Google Sheets
Verifique se a Service Account tem permissão de Editor na planilha.

## 📄 Licença

Uso interno TOTVS.

---

Desenvolvido com ❤️ para o RH TOTVS
