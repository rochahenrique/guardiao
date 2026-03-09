import { useState, useEffect, useRef } from 'react';
import { Send, Lightbulb, RotateCcw, CheckCircle2 } from 'lucide-react';
import { AvatarInova } from './AvatarInova';

interface Mensagem {
  id: string;
  tipo: 'agente' | 'usuario';
  conteudo: string;
  timestamp: Date;
}

interface EstadoChat {
  sessionId: string | null;
  mensagens: Mensagem[];
  progresso: number;
  carregando: boolean;
  finalizado: boolean;
  camposColetados: Record<string, any>;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [estado, setEstado] = useState<EstadoChat>({
    sessionId: null,
    mensagens: [],
    progresso: 0,
    carregando: false,
    finalizado: false,
    camposColetados: {},
  });

  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
  }, [estado.carregando, estado.mensagens]);

  const adicionarMensagem = (tipo: 'agente' | 'usuario', conteudo: string) => {
    const id = Date.now().toString();
    const novaMensagem: Mensagem = {
      id,
      tipo,
      conteudo,
      timestamp: new Date(),
    };
    setEstado(prev => ({
      ...prev,
      mensagens: [...prev.mensagens, novaMensagem],
    }));
  };

  const iniciar = async () => {
    setEstado(prev => ({ ...prev, carregando: true }));
    
    try {
      const response = await fetch(`${API_URL}/iniciar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      const data = await response.json();
      
      setEstado(prev => ({
        ...prev,
        sessionId: data.session_id,
        carregando: false,
      }));
      
      adicionarMensagem('agente', data.mensagem);
    } catch (error) {
      console.error('Erro ao iniciar:', error);
      adicionarMensagem('agente', 'Ops, tive um probleminha pra conectar. Tenta de novo?');
      setEstado(prev => ({ ...prev, carregando: false }));
    }
  };

  const enviar = async () => {
    if (!estado.sessionId || estado.carregando || !inputValue.trim()) return;

    const mensagemUsuario = inputValue.trim();
    setInputValue('');
    adicionarMensagem('usuario', mensagemUsuario);
    setEstado(prev => ({ ...prev, carregando: true }));

    try {
      const response = await fetch(`${API_URL}/mensagem`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: estado.sessionId,
          mensagem: mensagemUsuario
        })
      });

      const data = await response.json();

      setEstado(prev => ({
        ...prev,
        progresso: data.progresso,
        finalizado: data.finalizado,
        camposColetados: data.campos_coletados,
        carregando: false,
      }));

      adicionarMensagem('agente', data.mensagem);
    } catch (error) {
      console.error('Erro ao enviar:', error);
      adicionarMensagem('agente', 'Ih, deu um erro aqui. Pode repetir?');
      setEstado(prev => ({ ...prev, carregando: false }));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  const reiniciar = () => {
    setEstado({
      sessionId: null,
      mensagens: [],
      progresso: 0,
      carregando: false,
      finalizado: false,
      camposColetados: {},
    });
    setInputValue('');
  };

  const formatarMensagem = (conteudo: string) => {
    return conteudo.split('\n').map((linha, i) => {
      const partes = linha.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={i}>
          {partes.map((parte, j) => {
            if (parte.startsWith('**') && parte.endsWith('**')) {
              return <strong key={j}>{parte.slice(2, -2)}</strong>;
            }
            return parte;
          })}
          {i < conteudo.split('\n').length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="glass border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AvatarInova tamanho="md" />
            <div>
              <h1 className="font-display font-semibold text-white text-lg">
                Inova
              </h1>
              <p className="text-xs text-gray-400">Guardião de Ideias do RH</p>
            </div>
          </div>
          
          {estado.sessionId && !estado.finalizado && (
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-xs text-gray-400">Informações coletadas</p>
                <p className="text-sm font-medium text-white">{estado.progresso}%</p>
              </div>
              <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-totvs-primary to-totvs-accent transition-all duration-500"
                  style={{ width: `${estado.progresso}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-3xl w-full mx-auto flex flex-col">
        {!estado.sessionId ? (
          // Tela inicial
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-lg animate-fade-in">
              <div className="mx-auto mb-6">
                <AvatarInova tamanho="lg" />
              </div>
              
              <h2 className="font-display text-3xl font-bold gradient-text mb-4">
                Bora melhorar o RH juntos?
              </h2>
              
              <p className="text-gray-400 mb-8 leading-relaxed">
                Oi! Eu sou a Inova, e tô aqui pra ouvir suas ideias! 
                Conta pra mim o que poderia funcionar melhor no seu dia a dia.
                Vamos bater um papo informal, sem formulário chato. 😊
              </p>
              
              <button
                onClick={iniciar}
                disabled={estado.carregando}
                className="px-8 py-4 bg-gradient-to-r from-totvs-primary to-totvs-accent text-white font-semibold rounded-xl hover:opacity-90 transition-all transform hover:scale-105 disabled:opacity-50 disabled:transform-none flex items-center gap-2 mx-auto"
              >
                {estado.carregando ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Conectando...
                  </>
                ) : (
                  <>
                    <Lightbulb className="w-5 h-5" />
                    Começar a conversa
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
                  {msg.tipo === 'agente' && (
                    <div className="mr-2 flex-shrink-0">
                      <AvatarInova tamanho="sm" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                      msg.tipo === 'usuario'
                        ? 'bg-gradient-to-r from-totvs-primary to-totvs-accent text-white'
                        : 'glass text-gray-100'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{formatarMensagem(msg.conteudo)}</p>
                  </div>
                </div>
              ))}

              {estado.carregando && (
                <div className="flex justify-start animate-fade-in">
                  <div className="mr-2 flex-shrink-0">
                    <AvatarInova tamanho="sm" />
                  </div>
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
            {!estado.finalizado && (
              <div className="glass border-t border-white/10 p-4">
                <div className="flex gap-3">
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Digite sua mensagem..."
                    rows={1}
                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-totvs-primary resize-none"
                    style={{ minHeight: '48px', maxHeight: '120px' }}
                    onInput={(e) => {
                      const target = e.target as HTMLTextAreaElement;
                      target.style.height = 'auto';
                      target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                    }}
                  />
                  <button
                    onClick={enviar}
                    disabled={estado.carregando || !inputValue.trim()}
                    className="px-4 py-3 bg-gradient-to-r from-totvs-primary to-totvs-accent text-white font-medium rounded-xl hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Pressione Enter para enviar • Shift+Enter para nova linha
                </p>
              </div>
            )}

            {/* Finalizado */}
            {estado.finalizado && (
              <div className="glass border-t border-white/10 p-6 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-totvs-accent to-totvs-primary flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Conversa registrada!
                </h3>
                <p className="text-gray-400 mb-4">
                  Valeu demais por compartilhar! 🚀
                </p>
                <button
                  onClick={reiniciar}
                  className="px-6 py-3 bg-white/10 text-white font-medium rounded-xl hover:bg-white/20 transition-all flex items-center gap-2 mx-auto"
                >
                  <RotateCcw className="w-4 h-4" />
                  Nova conversa
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="glass border-t border-white/10 py-3">
        <p className="text-center text-xs text-gray-500">
          © {new Date().getFullYear()} TOTVS • Inova - Guardião de Ideias do RH
        </p>
      </footer>
    </div>
  );
}

export default App;
