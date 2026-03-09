"""
Agente de Coleta de Ideias de Inovação - Backend
TOTVS RH - Oportunidades de Processos
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime
import uuid

app = FastAPI(
    title="Agente de Inovação TOTVS",
    description="Coleta de oportunidades e dores de processos",
    version="1.0.0"
)

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente do proxy DTA
client = OpenAI(
    base_url=os.getenv("DTA_PROXY_URL", "https://proxy.dta.totvs.ai"),
    api_key=os.getenv("DTA_API_KEY", "sk-Q2m_kNH3orWeZX611razEQ"),
)

# Configuração Google Sheets (opcional)
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# ============================================
# DEFINIÇÃO DAS PERGUNTAS DO FORMULÁRIO
# ============================================

PERGUNTAS = [
    {
        "id": "processo",
        "secao": 1,
        "titulo": "Oportunidades de processos",
        "pergunta": "Qual o processo está sendo analisado?",
        "tipo": "texto_curto",
        "obrigatoria": True
    },
    {
        "id": "email",
        "secao": 1,
        "titulo": "Oportunidades de processos",
        "pergunta": "Qual é o seu email corporativo?",
        "tipo": "email",
        "obrigatoria": True
    },
    {
        "id": "resumo_dor",
        "secao": 1,
        "titulo": "Oportunidades de processos",
        "pergunta": "Faça um resumo da dor ou oportunidade identificada no processo.",
        "tipo": "texto_longo",
        "obrigatoria": True
    },
    {
        "id": "criticidade",
        "secao": 2,
        "titulo": "Impacto da oportunidade ou dor",
        "pergunta": "Qual o nível de criticidade desse processo para a área responsável/Companhia?",
        "tipo": "multipla_escolha",
        "opcoes": [
            "Muito baixo: Impacto marginal (luxo ou refinamento). Não compromete resultados ou apresenta riscos significativos.",
            "Baixo: Causa pequenos inconvenientes ou perda mínima de tempo. Impacto baixo; sem risco legal ou financeiro.",
            "Médio: Causa impacto notável na eficiência de uma equipe ou subprocesso. Gera erros ocasionais ou ineficiências.",
            "Alto: Impacto significativo em objetivos estratégicos ou grande volume de colaboradores. Causa erros frequentes.",
            "Muito Alto: Alto risco de compliance, financeiro/legal, paralisação de operações essenciais de RH ou tecnologia."
        ],
        "obrigatoria": True
    },
    {
        "id": "descricao_impacto",
        "secao": 2,
        "titulo": "Impacto da oportunidade ou dor",
        "pergunta": "Descreva o impacto dessa dor/oportunidade no processo (tempo de execução, eficiência, outros).",
        "tipo": "texto_longo",
        "obrigatoria": True
    },
    {
        "id": "pessoas_impactadas",
        "secao": 2,
        "titulo": "Impacto da oportunidade ou dor",
        "pergunta": "Caso essa dor seja minimizada ou a oportunidade seja aproveitada, quantas pessoas seriam impactadas diretamente?",
        "tipo": "multipla_escolha",
        "opcoes": [
            "Até 3 pessoas",
            "De 4 a 10 pessoas",
            "Acima de 10 pessoas"
        ],
        "obrigatoria": True
    },
    {
        "id": "outros_ganhos",
        "secao": 2,
        "titulo": "Impacto da oportunidade ou dor",
        "pergunta": "Caso essa dor seja minimizada ou a oportunidade seja aproveitada, há outros ganhos que você acredita que teríamos para a área/companhia?",
        "tipo": "texto_longo",
        "obrigatoria": False
    },
    {
        "id": "impacta_outros",
        "secao": 2,
        "titulo": "Impacto da oportunidade ou dor",
        "pergunta": "Quando você executa esse processo, ele gera algum resultado ou entrega que impacta outros processos?",
        "tipo": "multipla_escolha",
        "opcoes": [
            "Não",
            "Sim, impacta outro processo",
            "Sim, impacta 2 ou mais processos ou seu resultado agrega ao planejamento estratégico"
        ],
        "obrigatoria": True
    },
    {
        "id": "horas_economizadas",
        "secao": 3,
        "titulo": "Complexidade",
        "pergunta": "Em média, quantas horas por mês você estima que seriam economizadas caso essa oportunidade/dor seja implementada/mitigada? Considere o valor total, contemplando todas as pessoas envolvidas.",
        "tipo": "multipla_escolha",
        "opcoes": [
            "Menos de 2h/mês",
            "De 2h/mês a 5h/mês",
            "De 5h/mês a 10h/mês",
            "De 10h/mês a 15h/mês",
            "De 15h/mês a 20h/mês",
            "Acima de 20h/mês"
        ],
        "obrigatoria": True
    },
    {
        "id": "tipo_impacto",
        "secao": 3,
        "titulo": "Complexidade",
        "pergunta": "Que tipo de impacto essa oportunidade/dor melhora/mitiga caso seja implementada?",
        "tipo": "checkbox",
        "opcoes": [
            "Nenhum impacto relevante",
            "Impacto operacional na minha área",
            "Impacto operacional no RH como um todo",
            "Impacto em outros times TOTVS",
            "Impacto legal, financeiro ou reputacional",
            "Impacto em nossos clientes/Ecossistema TOTVS"
        ],
        "obrigatoria": True
    },
    {
        "id": "envolvimento_areas",
        "secao": 3,
        "titulo": "Complexidade",
        "pergunta": "Para implementar/mitigar essa oportunidade/dor é necessário o envolvimento de outras áreas da empresa ou RH?",
        "tipo": "checkbox",
        "opcoes": [
            "Não",
            "Sim, pouco envolvimento de outras áreas do RH",
            "Sim, pouco envolvimento de outras áreas da empresa",
            "Sim, muito envolvimento de outras áreas do RH",
            "Sim, muito envolvimento de outras áreas da empresa"
        ],
        "obrigatoria": True
    },
    {
        "id": "elementos_envolvidos",
        "secao": 3,
        "titulo": "Complexidade",
        "pergunta": "Há o envolvimento de algum destes elementos na oportunidade/dor identificada?",
        "tipo": "checkbox",
        "opcoes": [
            "Sistema Integrado (ATS, RM, Unit, Feedz...)",
            "Planilhas compartilhadas",
            "E-mail",
            "Papel/anotações físicas",
            "Etapas manuais",
            "Etapas repetitivas ou simples de executar",
            "Nenhum",
            "Outro"
        ],
        "obrigatoria": True
    },
    {
        "id": "solucao_pensada",
        "secao": 4,
        "titulo": "Solução",
        "pergunta": "Você já pensou em alguma solução? Se sim, qual?",
        "tipo": "texto_longo",
        "obrigatoria": False
    }
]

# ============================================
# MODELOS PYDANTIC
# ============================================

class IniciarSessaoRequest(BaseModel):
    email: Optional[str] = None

class IniciarSessaoResponse(BaseModel):
    session_id: str
    mensagem: str
    pergunta_atual: dict
    total_perguntas: int

class EnviarRespostaRequest(BaseModel):
    session_id: str
    resposta: Any  # Pode ser string ou lista (para checkbox)

class EnviarRespostaResponse(BaseModel):
    mensagem: str
    proxima_pergunta: Optional[dict]
    progresso: int
    total_perguntas: int
    finalizado: bool
    resumo: Optional[dict] = None

class ValidarEmailRequest(BaseModel):
    email: EmailStr

class ValidarEmailResponse(BaseModel):
    autorizado: bool
    mensagem: str

# ============================================
# ARMAZENAMENTO EM MEMÓRIA (SESSÕES)
# ============================================

sessoes: dict = {}

# Lista de emails autorizados (pode vir de Firestore/banco)
EMAILS_AUTORIZADOS = os.getenv("EMAILS_AUTORIZADOS", "").split(",")
VALIDAR_EMAIL = os.getenv("VALIDAR_EMAIL", "false").lower() == "true"

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def gerar_mensagem_ia(contexto: str, pergunta: dict) -> str:
    """Usa a IA para gerar uma mensagem amigável para a pergunta."""
    
    prompt = f"""Você é um assistente amigável da TOTVS que está coletando ideias de inovação dos colaboradores.

Contexto da conversa até agora:
{contexto}

Agora você precisa fazer a seguinte pergunta de forma natural e conversacional:
- Pergunta: {pergunta['pergunta']}
- Tipo: {pergunta['tipo']}
{"- Opções: " + ", ".join(pergunta.get('opcoes', [])) if pergunta.get('opcoes') else ""}

Regras:
1. Seja amigável e profissional
2. Se for a primeira pergunta, dê boas-vindas brevemente
3. Se houver opções, liste-as de forma clara (use números)
4. Não repita o que já foi dito
5. Mantenha a mensagem concisa (máximo 3 frases + opções se houver)
6. Para checkbox, informe que pode selecionar múltiplas opções

Responda apenas com a mensagem para o usuário:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Ajuste conforme modelo disponível no proxy
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback sem IA
        msg = pergunta['pergunta']
        if pergunta.get('opcoes'):
            msg += "\n\nOpções:\n"
            for i, opcao in enumerate(pergunta['opcoes'], 1):
                msg += f"{i}. {opcao}\n"
            if pergunta['tipo'] == 'checkbox':
                msg += "\n(Você pode selecionar múltiplas opções, separadas por vírgula)"
        return msg


def validar_resposta(resposta: Any, pergunta: dict) -> tuple[bool, str]:
    """Valida a resposta do usuário."""
    
    if pergunta['obrigatoria'] and not resposta:
        return False, "Esta pergunta é obrigatória. Por favor, forneça uma resposta."
    
    if not resposta and not pergunta['obrigatoria']:
        return True, ""
    
    if pergunta['tipo'] == 'email':
        if '@' not in str(resposta) or '.' not in str(resposta):
            return False, "Por favor, forneça um email válido."
    
    if pergunta['tipo'] == 'multipla_escolha':
        opcoes = pergunta.get('opcoes', [])
        # Aceita número ou texto
        if isinstance(resposta, int) or (isinstance(resposta, str) and resposta.isdigit()):
            idx = int(resposta) - 1
            if idx < 0 or idx >= len(opcoes):
                return False, f"Por favor, escolha uma opção entre 1 e {len(opcoes)}."
        elif resposta not in opcoes:
            # Tenta match parcial
            match = None
            for opcao in opcoes:
                if resposta.lower() in opcao.lower():
                    match = opcao
                    break
            if not match:
                return False, f"Opção não reconhecida. Escolha um número de 1 a {len(opcoes)}."
    
    if pergunta['tipo'] == 'checkbox':
        opcoes = pergunta.get('opcoes', [])
        if isinstance(resposta, str):
            # Converte string separada por vírgula em lista
            respostas = [r.strip() for r in resposta.split(',')]
        else:
            respostas = resposta if isinstance(resposta, list) else [resposta]
        
        for r in respostas:
            if isinstance(r, int) or (isinstance(r, str) and r.isdigit()):
                idx = int(r) - 1
                if idx < 0 or idx >= len(opcoes):
                    return False, f"Opção {r} inválida. Escolha entre 1 e {len(opcoes)}."
            elif r not in opcoes:
                # Tenta match parcial
                match = None
                for opcao in opcoes:
                    if r.lower() in opcao.lower():
                        match = opcao
                        break
                if not match:
                    return False, f"Opção '{r}' não reconhecida."
    
    return True, ""


def normalizar_resposta(resposta: Any, pergunta: dict) -> Any:
    """Normaliza a resposta para o formato correto."""
    
    if pergunta['tipo'] == 'multipla_escolha':
        opcoes = pergunta.get('opcoes', [])
        if isinstance(resposta, int) or (isinstance(resposta, str) and resposta.isdigit()):
            idx = int(resposta) - 1
            return opcoes[idx]
        # Match parcial
        for opcao in opcoes:
            if str(resposta).lower() in opcao.lower():
                return opcao
        return resposta
    
    if pergunta['tipo'] == 'checkbox':
        opcoes = pergunta.get('opcoes', [])
        if isinstance(resposta, str):
            respostas = [r.strip() for r in resposta.split(',')]
        else:
            respostas = resposta if isinstance(resposta, list) else [resposta]
        
        resultado = []
        for r in respostas:
            if isinstance(r, int) or (isinstance(r, str) and r.isdigit()):
                idx = int(r) - 1
                resultado.append(opcoes[idx])
            else:
                # Match parcial
                for opcao in opcoes:
                    if str(r).lower() in opcao.lower():
                        resultado.append(opcao)
                        break
                else:
                    resultado.append(r)
        return resultado
    
    return resposta


def salvar_google_sheets(respostas: dict) -> bool:
    """Salva as respostas no Google Sheets."""
    
    if not GOOGLE_SHEETS_ENABLED:
        return False
    
    try:
        # Configurar credenciais
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            print("GOOGLE_CREDENTIALS_JSON não configurado")
            return False
        
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
        
        # Preparar linha
        linha = [
            datetime.now().isoformat(),
            respostas.get('email', ''),
            respostas.get('processo', ''),
            respostas.get('resumo_dor', ''),
            respostas.get('criticidade', ''),
            respostas.get('descricao_impacto', ''),
            respostas.get('pessoas_impactadas', ''),
            respostas.get('outros_ganhos', ''),
            respostas.get('impacta_outros', ''),
            respostas.get('horas_economizadas', ''),
            ', '.join(respostas.get('tipo_impacto', [])) if isinstance(respostas.get('tipo_impacto'), list) else respostas.get('tipo_impacto', ''),
            ', '.join(respostas.get('envolvimento_areas', [])) if isinstance(respostas.get('envolvimento_areas'), list) else respostas.get('envolvimento_areas', ''),
            ', '.join(respostas.get('elementos_envolvidos', [])) if isinstance(respostas.get('elementos_envolvidos'), list) else respostas.get('elementos_envolvidos', ''),
            respostas.get('solucao_pensada', '')
        ]
        
        sheet.append_row(linha)
        return True
        
    except Exception as e:
        print(f"Erro ao salvar no Google Sheets: {e}")
        return False


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Agente de Inovação TOTVS"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/validar-email", response_model=ValidarEmailResponse)
async def validar_email(request: ValidarEmailRequest):
    """Valida se o email está autorizado a usar o sistema."""
    
    if not VALIDAR_EMAIL:
        return ValidarEmailResponse(
            autorizado=True,
            mensagem="Validação de email desabilitada."
        )
    
    email = request.email.lower().strip()
    
    # Verifica se é email TOTVS
    if not email.endswith("@totvs.com.br"):
        return ValidarEmailResponse(
            autorizado=False,
            mensagem="Apenas emails @totvs.com.br são permitidos."
        )
    
    # Se tiver lista específica, valida
    if EMAILS_AUTORIZADOS and EMAILS_AUTORIZADOS[0]:
        if email not in [e.lower().strip() for e in EMAILS_AUTORIZADOS]:
            return ValidarEmailResponse(
                autorizado=False,
                mensagem="Seu email não está na lista de autorizados. Entre em contato com o administrador."
            )
    
    return ValidarEmailResponse(
        autorizado=True,
        mensagem="Email autorizado!"
    )


@app.post("/iniciar", response_model=IniciarSessaoResponse)
async def iniciar_sessao(request: IniciarSessaoRequest):
    """Inicia uma nova sessão de coleta."""
    
    session_id = str(uuid.uuid4())
    
    sessoes[session_id] = {
        "pergunta_atual": 0,
        "respostas": {},
        "contexto": "",
        "iniciado_em": datetime.now().isoformat()
    }
    
    primeira_pergunta = PERGUNTAS[0]
    mensagem = gerar_mensagem_ia("Início da conversa", primeira_pergunta)
    
    return IniciarSessaoResponse(
        session_id=session_id,
        mensagem=mensagem,
        pergunta_atual=primeira_pergunta,
        total_perguntas=len(PERGUNTAS)
    )


@app.post("/responder", response_model=EnviarRespostaResponse)
async def enviar_resposta(request: EnviarRespostaRequest):
    """Recebe uma resposta e retorna a próxima pergunta."""
    
    if request.session_id not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessao = sessoes[request.session_id]
    idx_atual = sessao["pergunta_atual"]
    
    if idx_atual >= len(PERGUNTAS):
        raise HTTPException(status_code=400, detail="Formulário já finalizado")
    
    pergunta_atual = PERGUNTAS[idx_atual]
    
    # Validar resposta
    valido, erro = validar_resposta(request.resposta, pergunta_atual)
    if not valido:
        return EnviarRespostaResponse(
            mensagem=erro,
            proxima_pergunta=pergunta_atual,
            progresso=idx_atual,
            total_perguntas=len(PERGUNTAS),
            finalizado=False
        )
    
    # Normalizar e salvar resposta
    resposta_normalizada = normalizar_resposta(request.resposta, pergunta_atual)
    sessao["respostas"][pergunta_atual["id"]] = resposta_normalizada
    
    # Atualizar contexto
    sessao["contexto"] += f"\nPergunta: {pergunta_atual['pergunta']}\nResposta: {resposta_normalizada}\n"
    
    # Avançar para próxima pergunta
    sessao["pergunta_atual"] = idx_atual + 1
    
    # Verificar se finalizou
    if sessao["pergunta_atual"] >= len(PERGUNTAS):
        # Salvar no Google Sheets
        salvar_google_sheets(sessao["respostas"])
        
        return EnviarRespostaResponse(
            mensagem="🎉 Obrigado por compartilhar sua ideia de inovação! Suas respostas foram registradas com sucesso. A equipe de RH analisará sua contribuição.",
            proxima_pergunta=None,
            progresso=len(PERGUNTAS),
            total_perguntas=len(PERGUNTAS),
            finalizado=True,
            resumo=sessao["respostas"]
        )
    
    # Gerar próxima pergunta
    proxima_pergunta = PERGUNTAS[sessao["pergunta_atual"]]
    mensagem = gerar_mensagem_ia(sessao["contexto"], proxima_pergunta)
    
    return EnviarRespostaResponse(
        mensagem=mensagem,
        proxima_pergunta=proxima_pergunta,
        progresso=sessao["pergunta_atual"],
        total_perguntas=len(PERGUNTAS),
        finalizado=False
    )


@app.get("/sessao/{session_id}")
async def get_sessao(session_id: str):
    """Retorna o estado atual de uma sessão."""
    
    if session_id not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessao = sessoes[session_id]
    
    return {
        "session_id": session_id,
        "pergunta_atual": sessao["pergunta_atual"],
        "total_perguntas": len(PERGUNTAS),
        "respostas": sessao["respostas"],
        "finalizado": sessao["pergunta_atual"] >= len(PERGUNTAS)
    }


@app.get("/perguntas")
async def listar_perguntas():
    """Lista todas as perguntas do formulário."""
    return {"perguntas": PERGUNTAS, "total": len(PERGUNTAS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
