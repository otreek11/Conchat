import { useState, useEffect } from 'react';

interface ChatListItem {
  type: 'dm' | 'group';
  chatId: string;
  chatName: string;
  chatIcon?: string;
  lastMessage?: string;
}

function ChatsList() {
  const [chats] = useState<ChatListItem[]>([
    // Placeholder - será implementado com dados reais do backend futuramente
  ]);

  useEffect(() => {
    // Verificar se usuário está autenticado
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.hash = '#login';
    }
  }, []);

  const openChat = (type: 'dm' | 'group', chatId: string, chatName: string, chatIcon?: string) => {
    const params = new URLSearchParams({
      type,
      chatId,
      chatName,
      ...(chatIcon && { chatIcon }),
    });

    window.location.hash = `chat?${params.toString()}`;
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg-light)',
      padding: '2rem',
    }}>
      <h1 style={{ color: 'var(--secondary-teal)', marginBottom: '1rem' }}>
        Lista de Chats
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', textAlign: 'center' }}>
        Componente em desenvolvimento. Por enquanto, você pode testar o chat usando os botões abaixo.
      </p>

      {chats.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button
            onClick={() => openChat('dm', 'test-user-123', 'Usuário Teste')}
            style={{
              padding: '1rem 2rem',
              background: 'linear-gradient(135deg, var(--primary-cyan), var(--secondary-teal))',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
            }}
          >
            Abrir Chat Teste (DM)
          </button>

          <button
            onClick={() => openChat('group', 'test-group-456', 'Grupo Teste')}
            style={{
              padding: '1rem 2rem',
              background: 'linear-gradient(135deg, var(--primary-cyan), var(--secondary-teal))',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
            }}
          >
            Abrir Chat Teste (Grupo)
          </button>

          <button
            onClick={() => {
              localStorage.clear();
              window.location.hash = '#login';
            }}
            style={{
              padding: '1rem 2rem',
              background: 'var(--error-color)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              marginTop: '1rem',
            }}
          >
            Sair
          </button>
        </div>
      ) : (
        <div>
          {/* Lista de chats será implementada futuramente */}
        </div>
      )}
    </div>
  );
}

export default ChatsList;
