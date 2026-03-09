"""
Agente de Coleta de Ideias de Inovação - Backend v2.1
TOTVS RH - Conversa Natural com Extração Inteligente
Correções: Email obrigatório, validação de opções, campos obrigatórios
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime
import uuid

app = FastAPI(
    title="Agente de Inovação TOTVS v2.1",
    description="Coleta de oportunidades via conversa natural",
    version="2.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente OpenAI (Proxy DTA)
client = OpenAI(
    base_url=os.getenv("DTA_PROXY_URL", "https://proxy.dta.totvs.ai"),
    api_key=os.getenv("DTA_API_KEY", "sk-Q2m_kNH3orWeZX611razEQ"),
)

# Configurações
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# ============================================
# CAMPOS E OPÇÕES VÁLIDAS
# ============================================

CAMPOS_OBRIGATORIOS = [
    "processo",
    "email", 
    "resumo_dor",
    "criticidade",
    "descricao_impacto",
    "pessoas_impactadas",
    "impacta_outros",
    "horas_economizadas",
    "tipo_impacto",
    "envolvimento_areas",
    "elementos_envolvidos"
]

CAMPOS_OPCIONAIS = [
    "outros_ganhos",
    "solucao_pensada"
]

# Opções EXATAS para campos de múltipla escolha
OPCOES_VALIDAS = {
    "criticidade": [
        "Muito baixo",
        "Baixo", 
        "Médio",
        "Alto",
        "Muito Alto"
    ],
    "pessoas_impactadas": [
        "Até 3 pessoas",
        "De 4 a 10 pessoas",
        "Acima de 10 pessoas"
    ],
    "impacta_outros": [
        "Não",
        "Sim, impacta outro processo",
        "Sim, impacta 2 ou mais processos ou seu resultado agrega ao planejamento estratégico"
    ],
    "horas_economizadas": [
        "Menos de 2h/mês",
        "De 2h/mês a 5h/mês",
        "De 5h/mês a 10h/mês",
        "De 10h/mês a 15h/mês",
        "De 15h/mês a 20h/mês",
        "Acima de 20h/mês"
    ],
    "tipo_impacto": [
        "Nenhum impacto relevante",
        "Impacto operacional na minha área",
        "Impacto operacional no RH como um todo",
        "Impacto em outros times TOTVS",
        "Impacto legal, financeiro ou reputacional",
        "Impacto em nossos clientes/Ecossistema TOTVS"
    ],
    "envolvimento_areas": [
        "Não",
        "Sim, pouco envolvimento de outras áreas do RH",
        "Sim, pouco envolvimento de outras áreas da empresa",
        "Sim, muito envolvimento de outras áreas do RH",
        "Sim, muito envolvimento de outras áreas da empresa"
    ],
    "elementos_envolvidos": [
        "Sistema Integrado (ATS, RM, Unit, Feedz...)",
        "Planilhas compartilhadas",
        "E-mail",
        "Papel/anotações físicas",
        "Etapas manuais",
        "Etapas repetitivas ou simples de executar",
        "Nenhum",
        "Outro"
    ]
}

# ============================================
# MODELOS
# ============================================

class IniciarRequest(BaseModel):
    nome: Optional[str] = None

class IniciarResponse(BaseModel):
    session_id: str
    mensagem: str

class MensagemRequest(BaseModel):
    session_id: str
    mensagem: str

class MensagemResponse(BaseModel):
    mensagem: str
    campos_coletados: dict
    campos_faltando: list
    progresso: int
    finalizado: bool
    resumo: Optional[dict] = None

# ============================================
# ARMAZENAMENTO EM MEMÓRIA
# ============================================

sessoes: dict = {}

# ============================================
# FUNÇÕES DE IA
# ============================================

def gerar_resposta_conversa(historico: list, campos_coletados: dict, campos_faltando: list, fase: str) -> str:
    """Gera resposta natural baseada no histórico e campos que faltam coletar."""
    
    campos_faltando_str = ", ".join(campos_faltando[:3]) if campos_faltando else "nenhum"
    campos_coletados_str = json.dumps(campos_coletados, ensure_ascii=False, indent=2) if campos_coletados else "nenhum ainda"
    
    opcoes_json = json.dumps(OPCOES_VALIDAS, ensure_ascii=False, indent=2)
    
    system_prompt = f"""Você é a Inova, uma assistente virtual simpática da TOTVS que conversa informalmente para entender dores e oportunidades de melhoria nos processos do RH.

FASE ATUAL: {fase}

INFORMAÇÕES JÁ COLETADAS:
{campos_coletados_str}

INFORMAÇÕES QUE AINDA PRECISA COLETAR: {campos_faltando_str}

OPÇÕES VÁLIDAS PARA CAMPOS DE MÚLTIPLA ESCOLHA (USE EXATAMENTE ESTAS):
{opcoes_json}

REGRAS DE LINGUAGEM (MUITO IMPORTANTE):
1. Use LINGUAGEM NEUTRA DE GÊNERO - sem "cara", "mano", "amigo"
2. Em vez de "Cara, entendo...", diga "Nossa, entendo..." ou "Puxa, entendo..."
3. Use "você" normalmente
4. NÃO use neopronomes (elu, delu, etc)

REGRAS DE COLETA:
1. Se ainda NÃO tem o EMAIL, peça de forma natural: "Ah, me passa seu email corporativo pra eu registrar direitinho?"
2. Se ainda NÃO tem o PROCESSO, pergunte qual área/processo está analisando
3. Colete as informações de forma natural na conversa
4. Para campos de múltipla escolha, tente inferir a opção correta da lista de OPÇÕES VÁLIDAS
5. Quando perguntar sobre horas economizadas, criticidade, etc., dê exemplos das opções disponíveis

REGRAS DE CONVERSA:
1. Seja informal mas respeitosa
2. NUNCA faça perguntas de formulário tipo "Qual o nível de criticidade de 1 a 5?"
3. Pergunte de forma natural: "E isso tá atrapalhando muito o dia a dia? É algo urgente ou mais tranquilo?"
4. Use frases curtas, como em um chat
5. Máximo 2-3 frases por resposta

EXEMPLOS DE PERGUNTAS NATURAIS:
- Para criticidade: "E isso é algo urgente que tá travando o trabalho, ou é mais uma melhoria que seria legal ter?"
- Para horas: "Quanto tempo mais ou menos vocês perdem com isso por mês? Tipo, menos de 2 horas, umas 5 horas, ou é bem mais que isso?"
- Para pessoas impactadas: "E isso afeta só você ou tem mais gente passando por isso? Tipo, até umas 3 pessoas, ou é mais gente?"
- Para elementos: "E vocês usam o quê pra fazer isso hoje? Sistema, planilha, email, papel...?"

FORMATO: Responda apenas com sua mensagem, sem explicações."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(historico)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao gerar resposta: {e}")
        return "Desculpa, tive um probleminha aqui. Pode repetir o que você disse?"


def extrair_campos(historico: list, campos_atuais: dict) -> dict:
    """Extrai campos das mensagens do usuário."""
    
    mensagens_usuario = [m["content"] for m in historico if m["role"] == "user"]
    conversa_completa = "\n".join(mensagens_usuario)
    
    opcoes_json = json.dumps(OPCOES_VALIDAS, ensure_ascii=False, indent=2)
    
    prompt = f"""Analise esta conversa e extraia as informações em formato JSON.

CONVERSA DO USUÁRIO:
{conversa_completa}

CAMPOS JÁ EXTRAÍDOS ANTERIORMENTE:
{json.dumps(campos_atuais, ensure_ascii=False)}

OPÇÕES VÁLIDAS - USE EXATAMENTE UMA DESTAS PARA CADA CAMPO:
{opcoes_json}

EXTRAIA AS INFORMAÇÕES E RETORNE UM JSON:

{{
    "processo": "nome do processo/área mencionado",
    "email": "email corporativo se mencionado (deve conter @)",
    "resumo_dor": "resumo do problema/dor em 1-2 frases",
    "criticidade": "DEVE SER UMA DAS OPÇÕES: Muito baixo, Baixo, Médio, Alto, Muito Alto",
    "descricao_impacto": "descrição do impacto no trabalho",
    "pessoas_impactadas": "DEVE SER UMA DAS OPÇÕES: Até 3 pessoas, De 4 a 10 pessoas, Acima de 10 pessoas",
    "outros_ganhos": "outros benefícios mencionados",
    "impacta_outros": "DEVE SER UMA DAS OPÇÕES da lista impacta_outros",
    "horas_economizadas": "DEVE SER UMA DAS OPÇÕES da lista horas_economizadas",
    "tipo_impacto": ["LISTA de opções válidas de tipo_impacto que se aplicam"],
    "envolvimento_areas": "DEVE SER UMA DAS OPÇÕES da lista envolvimento_areas",
    "elementos_envolvidos": ["LISTA de opções válidas de elementos_envolvidos mencionados"],
    "solucao_pensada": "solução que a pessoa sugeriu"
}}

REGRAS IMPORTANTES:
1. Retorne APENAS o JSON, nada mais
2. Use null para campos não mencionados
3. Para campos com opções fixas, escolha EXATAMENTE uma das opções válidas listadas
4. Se não conseguir mapear para uma opção válida, use null
5. Para email, só extraia se contiver @ e parecer um email válido
6. Mantenha os valores já extraídos anteriormente se não houver nova informação"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2
        )
        
        resultado = response.choices[0].message.content.strip()
        
        # Limpar markdown se houver
        if "```json" in resultado:
            resultado = resultado.split("```json")[1].split("```")[0]
        elif "```" in resultado:
            resultado = resultado.split("```")[1].split("```")[0]
        
        novos_campos = json.loads(resultado)
        
        # Validar e mesclar campos
        for campo, valor in novos_campos.items():
            if valor is not None and valor != "" and valor != []:
                # Validar campos de múltipla escolha
                if campo in OPCOES_VALIDAS:
                    if isinstance(valor, list):
                        # Para campos que aceitam múltiplas opções
                        valores_validos = [v for v in valor if v in OPCOES_VALIDAS[campo]]
                        if valores_validos:
                            campos_atuais[campo] = valores_validos
                    else:
                        # Para campos de escolha única
                        if valor in OPCOES_VALIDAS[campo]:
                            campos_atuais[campo] = valor
                        else:
                            # Tentar encontrar a opção mais similar
                            valor_lower = valor.lower()
                            for opcao in OPCOES_VALIDAS[campo]:
                                if valor_lower in opcao.lower() or opcao.lower() in valor_lower:
                                    campos_atuais[campo] = opcao
                                    break
                else:
                    # Campos de texto livre
                    if campo == "email":
                        if "@" in str(valor):
                            campos_atuais[campo] = valor
                    else:
                        campos_atuais[campo] = valor
        
        return campos_atuais
        
    except Exception as e:
        print(f"Erro ao extrair campos: {e}")
        import traceback
        print(traceback.format_exc())
        return campos_atuais


def calcular_campos_faltando(campos_coletados: dict) -> list:
    """Calcula quais campos obrigatórios ainda faltam."""
    faltando = []
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in campos_coletados or not campos_coletados[campo]:
            faltando.append(campo)
    return faltando


def determinar_fase(campos_coletados: dict, historico: list) -> str:
    """Determina a fase atual da conversa."""
    if not campos_coletados.get("email"):
        return "COLETA_EMAIL"
    elif not campos_coletados.get("processo"):
        return "COLETA_PROCESSO"
    elif not campos_coletados.get("resumo_dor"):
        return "COLETA_DOR"
    elif len(historico) < 12:
        return "EXPLORACAO"
    else:
        return "FINALIZACAO"


def gerar_resumo_confirmacao(campos: dict) -> str:
    """Gera um resumo amigável para confirmação."""
    
    resumo = "📋 **Deixa eu ver se entendi tudo direitinho:**\n\n"
    
    if campos.get("processo"):
        resumo += f"**Processo/Área:** {campos['processo']}\n"
    
    if campos.get("email"):
        resumo += f"**Seu email:** {campos['email']}\n"
    
    if campos.get("resumo_dor"):
        resumo += f"**O problema:** {campos['resumo_dor']}\n"
    
    if campos.get("criticidade"):
        resumo += f"**Urgência:** {campos['criticidade']}\n"
    
    if campos.get("pessoas_impactadas"):
        resumo += f"**Pessoas afetadas:** {campos['pessoas_impactadas']}\n"
    
    if campos.get("horas_economizadas"):
        resumo += f"**Tempo que economizaria:** {campos['horas_economizadas']}\n"
    
    if campos.get("tipo_impacto"):
        if isinstance(campos['tipo_impacto'], list):
            resumo += f"**Tipo de impacto:** {', '.join(campos['tipo_impacto'])}\n"
        else:
            resumo += f"**Tipo de impacto:** {campos['tipo_impacto']}\n"
    
    if campos.get("elementos_envolvidos"):
        if isinstance(campos['elementos_envolvidos'], list):
            resumo += f"**Ferramentas envolvidas:** {', '.join(campos['elementos_envolvidos'])}\n"
        else:
            resumo += f"**Ferramentas envolvidas:** {campos['elementos_envolvidos']}\n"
    
    if campos.get("solucao_pensada"):
        resumo += f"**Sua ideia de solução:** {campos['solucao_pensada']}\n"
    
    # Verificar campos faltantes
    faltando = calcular_campos_faltando(campos)
    if faltando:
        resumo += f"\n⚠️ *Alguns campos ficaram em branco: {', '.join(faltando[:3])}{'...' if len(faltando) > 3 else ''}*\n"
    
    resumo += "\n**Tá tudo certo? Posso registrar assim?**"
    
    return resumo


def salvar_google_sheets(dados: dict) -> bool:
    """Salva os dados no Google Sheets."""
    
    if not GOOGLE_SHEETS_ENABLED:
        print("Google Sheets não está habilitado")
        return False
    
    try:
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
        
        # Formatar listas como string
        tipo_impacto = dados.get('tipo_impacto', '')
        if isinstance(tipo_impacto, list):
            tipo_impacto = ', '.join(tipo_impacto)
            
        envolvimento = dados.get('envolvimento_areas', '')
        if isinstance(envolvimento, list):
            envolvimento = ', '.join(envolvimento)
            
        elementos = dados.get('elementos_envolvidos', '')
        if isinstance(elementos, list):
            elementos = ', '.join(elementos)
        
        linha = [
            datetime.now().isoformat(),
            dados.get('email', ''),
            dados.get('processo', ''),
            dados.get('resumo_dor', ''),
            dados.get('criticidade', ''),
            dados.get('descricao_impacto', ''),
            dados.get('pessoas_impactadas', ''),
            dados.get('outros_ganhos', ''),
            dados.get('impacta_outros', ''),
            dados.get('horas_economizadas', ''),
            tipo_impacto,
            envolvimento,
            elementos,
            dados.get('solucao_pensada', '')
        ]
        
        sheet.append_row(linha)
        print(f"Dados salvos no Google Sheets: {linha}")
        return True
        
    except Exception as e:
        import traceback
        print(f"Erro ao salvar no Google Sheets: {e}")
        print(traceback.format_exc())
        return False


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Agente de Inovação TOTVS v2.1"}


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.1.0"}


@app.post("/iniciar", response_model=IniciarResponse)
async def iniciar_sessao(request: IniciarRequest):
    """Inicia uma nova conversa."""
    
    session_id = str(uuid.uuid4())
    
    mensagem_inicial = """Oi! 👋 Tudo bem?

Eu sou a Inova, e tô aqui pra ouvir suas ideias sobre melhorias nos processos do RH!

Antes de começar, me passa seu **email corporativo** pra eu registrar direitinho? 📧"""

    sessoes[session_id] = {
        "historico": [
            {"role": "assistant", "content": mensagem_inicial}
        ],
        "campos_coletados": {},
        "iniciado_em": datetime.now().isoformat(),
        "finalizado": False,
        "aguardando_confirmacao": False
    }
    
    return IniciarResponse(
        session_id=session_id,
        mensagem=mensagem_inicial
    )


@app.post("/mensagem", response_model=MensagemResponse)
async def enviar_mensagem(request: MensagemRequest):
    """Processa mensagem do usuário e responde naturalmente."""
    
    if request.session_id not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessao = sessoes[request.session_id]
    
    if sessao["finalizado"]:
        return MensagemResponse(
            mensagem="Essa conversa já foi finalizada! Se quiser compartilhar outra ideia, é só começar uma nova conversa. 😊",
            campos_coletados=sessao["campos_coletados"],
            campos_faltando=[],
            progresso=100,
            finalizado=True,
            resumo=sessao["campos_coletados"]
        )
    
    # Adicionar mensagem do usuário ao histórico
    sessao["historico"].append({
        "role": "user",
        "content": request.mensagem
    })
    
    # Extrair campos da conversa
    sessao["campos_coletados"] = extrair_campos(
        sessao["historico"], 
        sessao["campos_coletados"]
    )
    
    # Log para debug
    print(f"Campos coletados: {json.dumps(sessao['campos_coletados'], ensure_ascii=False)}")
    
    # Calcular progresso
    campos_faltando = calcular_campos_faltando(sessao["campos_coletados"])
    total_campos = len(CAMPOS_OBRIGATORIOS)
    campos_preenchidos = total_campos - len(campos_faltando)
    progresso = int((campos_preenchidos / total_campos) * 100)
    
    # Determinar fase
    fase = determinar_fase(sessao["campos_coletados"], sessao["historico"])
    
    # Verificar se está aguardando confirmação
    if sessao.get("aguardando_confirmacao"):
        msg_lower = request.mensagem.lower()
        if any(palavra in msg_lower for palavra in ["sim", "isso", "correto", "certo", "pode", "confirmo", "ok", "yes", "tá", "está", "isso mesmo"]):
            # Confirmar e salvar
            salvar_google_sheets(sessao["campos_coletados"])
            sessao["finalizado"] = True
            
            return MensagemResponse(
                mensagem="🎉 Maravilha! Registrei tudo certinho!\n\nMuito obrigada por compartilhar! Sua contribuição é super importante pra gente melhorar os processos do RH.\n\nSe tiver mais alguma ideia no futuro, é só voltar aqui! 💡",
                campos_coletados=sessao["campos_coletados"],
                campos_faltando=[],
                progresso=100,
                finalizado=True,
                resumo=sessao["campos_coletados"]
            )
        elif any(palavra in msg_lower for palavra in ["não", "errado", "corrigir", "mudar", "ajustar", "falta"]):
            sessao["aguardando_confirmacao"] = False
            resposta = "Sem problemas! Me conta o que precisa ajustar que eu corrijo aqui. 😊"
        else:
            resposta = "Só pra confirmar: as informações estão certas? Posso registrar assim? (responde 'sim' ou me fala o que precisa ajustar)"
        
        sessao["historico"].append({"role": "assistant", "content": resposta})
        
        return MensagemResponse(
            mensagem=resposta,
            campos_coletados=sessao["campos_coletados"],
            campos_faltando=campos_faltando,
            progresso=progresso,
            finalizado=False
        )
    
    # Verificar se deve pedir confirmação
    # Só pede confirmação se tem os campos essenciais E já conversou bastante
    campos_essenciais = ["processo", "resumo_dor", "email"]
    tem_essenciais = all(sessao["campos_coletados"].get(c) for c in campos_essenciais)
    
    if tem_essenciais and len(sessao["historico"]) >= 10 and len(campos_faltando) <= 4:
        sessao["aguardando_confirmacao"] = True
        resposta = gerar_resumo_confirmacao(sessao["campos_coletados"])
        sessao["historico"].append({"role": "assistant", "content": resposta})
        
        return MensagemResponse(
            mensagem=resposta,
            campos_coletados=sessao["campos_coletados"],
            campos_faltando=campos_faltando,
            progresso=progresso,
            finalizado=False
        )
    
    # Gerar resposta natural da conversa
    resposta = gerar_resposta_conversa(
        sessao["historico"],
        sessao["campos_coletados"],
        campos_faltando,
        fase
    )
    
    # Adicionar resposta ao histórico
    sessao["historico"].append({
        "role": "assistant", 
        "content": resposta
    })
    
    return MensagemResponse(
        mensagem=resposta,
        campos_coletados=sessao["campos_coletados"],
        campos_faltando=campos_faltando,
        progresso=progresso,
        finalizado=False
    )


@app.post("/finalizar")
async def finalizar_conversa(request: MensagemRequest):
    """Força a finalização da conversa e mostra resumo."""
    
    if request.session_id not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessao = sessoes[request.session_id]
    sessao["aguardando_confirmacao"] = True
    
    resumo = gerar_resumo_confirmacao(sessao["campos_coletados"])
    campos_faltando = calcular_campos_faltando(sessao["campos_coletados"])
    
    return MensagemResponse(
        mensagem=resumo,
        campos_coletados=sessao["campos_coletados"],
        campos_faltando=campos_faltando,
        progresso=100,
        finalizado=False
    )


@app.get("/sessao/{session_id}")
async def get_sessao(session_id: str):
    """Retorna estado da sessão."""
    
    if session_id not in sessoes:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessao = sessoes[session_id]
    campos_faltando = calcular_campos_faltando(sessao["campos_coletados"])
    
    return {
        "session_id": session_id,
        "campos_coletados": sessao["campos_coletados"],
        "campos_faltando": campos_faltando,
        "historico": sessao["historico"],
        "finalizado": sessao["finalizado"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)