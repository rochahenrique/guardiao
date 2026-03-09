import { IniciarSessaoResponse, EnviarRespostaResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export async function iniciarSessao(): Promise<IniciarSessaoResponse> {
  const response = await fetch(`${API_URL}/iniciar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    throw new Error('Erro ao iniciar sessão');
  }

  return response.json();
}

export async function enviarResposta(
  sessionId: string,
  resposta: string | string[]
): Promise<EnviarRespostaResponse> {
  const response = await fetch(`${API_URL}/responder`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      resposta,
    }),
  });

  if (!response.ok) {
    throw new Error('Erro ao enviar resposta');
  }

  return response.json();
}

export async function validarEmail(email: string): Promise<{ autorizado: boolean; mensagem: string }> {
  const response = await fetch(`${API_URL}/validar-email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new Error('Erro ao validar email');
  }

  return response.json();
}
