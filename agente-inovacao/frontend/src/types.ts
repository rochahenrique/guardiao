export interface Pergunta {
  id: string;
  secao: number;
  titulo: string;
  pergunta: string;
  tipo: 'texto_curto' | 'texto_longo' | 'email' | 'multipla_escolha' | 'checkbox';
  opcoes?: string[];
  obrigatoria: boolean;
}

export interface IniciarSessaoResponse {
  session_id: string;
  mensagem: string;
  pergunta_atual: Pergunta;
  total_perguntas: number;
}

export interface EnviarRespostaResponse {
  mensagem: string;
  proxima_pergunta: Pergunta | null;
  progresso: number;
  total_perguntas: number;
  finalizado: boolean;
  resumo?: Record<string, unknown>;
}

export interface Mensagem {
  id: string;
  tipo: 'agente' | 'usuario';
  conteudo: string;
  timestamp: Date;
  pergunta?: Pergunta;
}

export interface EstadoChat {
  sessionId: string | null;
  mensagens: Mensagem[];
  perguntaAtual: Pergunta | null;
  progresso: number;
  totalPerguntas: number;
  carregando: boolean;
  finalizado: boolean;
}
