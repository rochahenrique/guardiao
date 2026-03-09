import { useState, useEffect, useRef } from 'react';
import { Send, Lightbulb, CheckCircle2, Sparkles, RotateCcw } from 'lucide-react';
import { Mensagem, Pergunta, EstadoChat } from './types';
import { iniciarSessao, enviarResposta } from './api';

function App() {
  const [estado, setEstado] = useState<EstadoChat>({
    sessionId: null,
    mensagens: [],
    perguntaAtual: null,
    progresso: 0,
    totalPerguntas: 13,
    carregando: false,
    finalizado: false,
  });

  const [inputValue, setInputValue] = useState('');
  const [selectedOptions, setSelectedOptions] = useState<number[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [estado.mensagens]);

  useEffect(() => {
    if (!estado.carregando && inputRef.current) {
      inputRef.current.focus();
    }
  }, [estado.carregando, estado.perguntaAtual]);

  const adicionarMensagem = (tipo: 'agente' | 'usuario', conteudo: string, pergunta?: Pergunta) => {
    const novaMensagem: Mensagem = {
      id: Date.now().toString(),
      tipo,
      conteudo,
      timestamp: new Date(),
      pergunta,
    };
    setEstado(prev => ({
      ...prev,
      mensagens: [...prev.mensagens, novaMensagem],
    }));
  };

  const iniciar = async () => {
    setEstado(prev => ({ ...prev, carregando: true }));
    
    try {
      const response = await iniciarSessao();
      
      setEstado(prev => ({
        ...prev,
        sessionId: response.session_id,
        perguntaAtual: response.pergunta_atual,
        totalPerguntas: response.total_perguntas,
        carregando: false,
      }));
      
      adicionarMensagem('agente', response.mensagem, response.pergunta_atual);
    } catch (error) {
      console.error('Erro ao iniciar:', error);
      adicionarMensagem('agente', 'Desculpe, ocorreu um erro ao iniciar. Por favor, tente novamente.');
      setEstado(prev => ({ ...prev, carregando: false }));
    }
  };

  const enviar = async () => {
    if (!estado.sessionId || estado.carregando) return;

    const pergunta = estado.perguntaAtual;
    if (!pergunta) return;

    let resposta: string | string[];

    if (pergunta.tipo === 'checkbox' || pergunta.tipo === 'multipla_escolha') {
      if (selectedOptions.length === 0) {
        if (pergunta.obrigatoria) {
          adicionarMensagem('agente', 'Por favor, selecione pelo menos uma opção.');
          return;
        }
        resposta = '';
      } else if (pergunta.tipo === 'checkbox') {
        resposta = selectedOptions.map(i => (i + 1).toString());
      } else {
        resposta = (selectedOptions[0] + 1).toString();
      }
    } else {
      if (!inputValue.trim() && pergunta.obrigatoria) {
        adicionarMensagem('agente', 'Esta pergunta é obrigatória. Por favor, forneça uma resposta.');
        return;
      }
      resposta = inputValue.trim();
    }

    // Mostrar resposta do usuário
    const respostaExibicao = pergunta.tipo === 'checkbox' || pergunta.tipo === 'multipla_escolha'
      ? selectedOptions.map(i => pergunta.opcoes?.[i] || '').join(', ')
      : inputValue;
    
    if (respostaExibicao) {
      adicionarMensagem('usuario', respostaExibicao);
    }

    setInputValue('');
    setSelectedOptions([]);
    setEstado(prev => ({ ...prev, carregando: true }));

    try {
      const response = await enviarResposta(estado.sessionId, resposta);

      setEstado(prev => ({
        ...prev,
        perguntaAtual: response.proxima_pergunta,
        progresso: response.progresso,
        finalizado: response.finalizado,
        carregando: false,
      }));

      adicionarMensagem('agente', response.mensagem, response.proxima_pergunta || undefined);
    } catch (error) {
      console.error('Erro ao enviar:', error);
      adicionarMensagem('agente', 'Desculpe, ocorreu um erro. Por favor, tente novamente.');
      setEstado(prev => ({ ...prev, carregando: false }));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  const toggleOption = (index: number) => {
    const pergunta = estado.perguntaAtual;
    if (!pergunta) return;

    if (pergunta.tipo === 'multipla_escolha') {
      setSelectedOptions([index]);
    } else {
      setSelectedOptions(prev =>
        prev.includes(index)
          ? prev.filter(i => i !== index)
          : [...prev, index]
      );
    }
  };

  const reiniciar = () => {
    setEstado({
      sessionId: null,
      mensagens: [],
      perguntaAtual: null,
      progresso: 0,
      totalPerguntas: 13,
      carregando: false,
      finalizado: false,
    });
    setInputValue('');
    setSelectedOptions([]);
  };

  const progresso = estado.totalPerguntas > 0 
    ? (estado.progresso / estado.totalPerguntas) * 100 
    : 0;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="glass border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-totvs-primary to-totvs-accent flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display font-semibold text-white text-lg">
                Agente de Inovação
              </h1>
              <p className="text-xs text-gray-400">TOTVS RH • Oportunidades de Processos</p>
            </div>
          </div>
          
          {estado.sessionId && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-400">Progresso</p>
                <p className="text-sm font-medium text-white">
                  {estado.progresso} de {estado.totalPerguntas}
                </p>
              </div>
              <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-totvs-primary to-totvs-accent transition-all duration-500"
                  style={{ width: `${progresso}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl w-full mx-auto flex flex-col">
        {!estado.sessionId ? (
          // Tela inicial
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-lg animate-fade-in">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-totvs-primary to-totvs-accent flex items-center justify-center animate-pulse-glow">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              
              <h2 className="font-display text-3xl font-bold gradient-text mb-4">
                Compartilhe suas ideias de inovação
              </h2>
              
              <p className="text-gray-400 mb-8 leading-relaxed">
                Nosso objetivo é entender melhor as oportunidades e dores dos processos, 
                contemplando impacto e complexidade para a implementação ou mitigação. 
                Sua contribuição é essencial para a evolução do nosso RH!
              </p>
              
              <button
                onClick={iniciar}
                disabled={estado.carregando}
                className="px-8 py-4 bg-gradient-to-r from-totvs-primary to-totvs-accent text-white font-semibold rounded-xl hover:opacity-90 transition-all transform hover:scale-105 disabled:opacity-50 disabled:transform-none flex items-center gap-2 mx-auto"
              >
                {estado.carregando ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Iniciando...
                  </>
                ) : (
                  <>
                    <Lightbulb className="w-5 h-5" />
                    Começar a contribuir
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          // Chat
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {estado.mensagens.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.tipo === 'usuario' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.tipo === 'usuario'
                        ? 'bg-gradient-to-r from-totvs-primary to-totvs-accent text-white'
                        : 'glass text-gray-100'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.conteudo}</p>
                  </div>
                </div>
              ))}

              {estado.carregando && (
                <div className="flex justify-start animate-fade-in">
                  <div className="glass rounded-2xl px-4 py-3 flex items-center gap-2">
                    <div className="w-2 h-2 bg-totvs-primary rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-totvs-primary rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-totvs-primary rounded-full typing-dot" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            {!estado.finalizado && estado.perguntaAtual && (
              <div className="glass border-t border-white/10 p-4">
                {/* Opções para múltipla escolha ou checkbox */}
                {(estado.perguntaAtual.tipo === 'multipla_escolha' || 
                  estado.perguntaAtual.tipo === 'checkbox') && 
                  estado.perguntaAtual.opcoes && (
                  <div className="mb-4 space-y-2 max-h-60 overflow-y-auto">
                    {estado.perguntaAtual.opcoes.map((opcao, index) => (
                      <button
                        key={index}
                        onClick={() => toggleOption(index)}
                        className={`w-full text-left px-4 py-3 rounded-xl transition-all ${
                          selectedOptions.includes(index)
                            ? 'bg-gradient-to-r from-totvs-primary/20 to-totvs-accent/20 border-2 border-totvs-primary text-white'
                            : 'glass hover:bg-white/5 text-gray-300'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-5 h-5 rounded-${estado.perguntaAtual?.tipo === 'checkbox' ? 'md' : 'full'} border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                            selectedOptions.includes(index)
                              ? 'border-totvs-primary bg-totvs-primary'
                              : 'border-gray-500'
                          }`}>
                            {selectedOptions.includes(index) && (
                              <CheckCircle2 className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <span className="text-sm">{opcao}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* Input de texto */}
                {(estado.perguntaAtual.tipo === 'texto_curto' || 
                  estado.perguntaAtual.tipo === 'texto_longo' ||
                  estado.perguntaAtual.tipo === 'email') && (
                  <div className="mb-4">
                    {estado.perguntaAtual.tipo === 'texto_longo' ? (
                      <textarea
                        ref={inputRef as React.RefObject<HTMLTextAreaElement>}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="Digite sua resposta..."
                        rows={4}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-totvs-primary resize-none"
                      />
                    ) : (
                      <input
                        ref={inputRef as React.RefObject<HTMLInputElement>}
                        type={estado.perguntaAtual.tipo === 'email' ? 'email' : 'text'}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder={estado.perguntaAtual.tipo === 'email' ? 'seu.email@totvs.com.br' : 'Digite sua resposta...'}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-totvs-primary"
                      />
                    )}
                  </div>
                )}

                {/* Botão Enviar */}
                <div className="flex justify-end">
                  <button
                    onClick={enviar}
                    disabled={estado.carregando}
                    className="px-6 py-3 bg-gradient-to-r from-totvs-primary to-totvs-accent text-white font-medium rounded-xl hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                    Enviar
                  </button>
                </div>
              </div>
            )}

            {/* Finalizado */}
            {estado.finalizado && (
              <div className="glass border-t border-white/10 p-6 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-totvs-accent to-totvs-primary flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Contribuição registrada!
                </h3>
                <p className="text-gray-400 mb-4">
                  Obrigado por compartilhar sua ideia de inovação.
                </p>
                <button
                  onClick={reiniciar}
                  className="px-6 py-3 bg-white/10 text-white font-medium rounded-xl hover:bg-white/20 transition-all flex items-center gap-2 mx-auto"
                >
                  <RotateCcw className="w-4 h-4" />
                  Enviar nova ideia
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="glass border-t border-white/10 py-3">
        <p className="text-center text-xs text-gray-500">
          © {new Date().getFullYear()} TOTVS • Agente de Inovação RH
        </p>
      </footer>
    </div>
  );
}

export default App;
