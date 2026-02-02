import { useState, useEffect, useRef } from 'react';
import mqtt from 'mqtt';
import { v4 as uuidv4 } from 'uuid';
import './Chat.css';

type MqttClient = ReturnType<typeof mqtt.connect>;

type ChatType = 'dm' | 'group';

interface ChatParams {
  type: ChatType;
  chatId: string;
  chatName: string;
  chatIcon?: string;
}

interface Message {
  uuid: string;
  chatId: string;
  type: ChatType;
  from: string;
  content: string;
  timestamp: string;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
}

interface MqttEvent {
  type: 'MESSAGE_NEW' | 'MESSAGE_EDIT' | 'MESSAGE_DELETED' | 'MESSAGE_DELIVERED' | 'MESSAGE_READ';
  from: string;
  payload: {
    message_id?: string;
    content?: string;
    [key: string]: any;
  };
  timestamp: string;
}

interface CurrentUser {
  uuid: string;
  username: string;
  name: string;
  pfp_url?: string;
}

interface GroupMember {
  user_id: string;
  username: string;
  role: 'owner' | 'admin' | 'member';
}

const BASE_URL = 'http://localhost:8000/api/v1';

function Chat() {
  const [chatParams, setChatParams] = useState<ChatParams | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [mqttClient, setMqttClient] = useState<MqttClient | undefined>(undefined);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);

  // Parse parâmetros da URL
  useEffect(() => {
    const hash = window.location.hash.slice(1);

    if (!hash.startsWith('chat?')) {
      window.location.hash = '#chats';
      return;
    }

    const params = new URLSearchParams(hash.substring(5));
    const type = params.get('type') as ChatType;
    const chatId = params.get('chatId');
    const chatName = params.get('chatName');
    const chatIcon = params.get('chatIcon') || undefined;

    if (!type || !chatId || !chatName) {
      setError('Parâmetros inválidos');
      return;
    }

    setChatParams({ type, chatId, chatName, chatIcon });
  }, []);

  // Buscar usuário atual
  const fetchCurrentUser = async (): Promise<CurrentUser | null> => {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch user');

      const data = await response.json();
      const userUuid = data.uuid;

      const userResponse = await fetch(`${BASE_URL}/users/id/${userUuid}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!userResponse.ok) throw new Error('Failed to fetch user details');

      const userData = await userResponse.json();

      return {
        uuid: userUuid,
        username: userData.username,
        name: userData.name,
        pfp_url: userData.pfp_url,
      };
    } catch (error) {
      console.error('Error fetching current user:', error);
      setError('Erro ao carregar informações do usuário');
      return null;
    }
  };

  // Buscar membros do grupo
  const fetchGroupMembers = async (groupId: string): Promise<GroupMember[]> => {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${BASE_URL}/groups/${groupId}/members`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch members');

      const data = await response.json();

      const membersWithInfo = await Promise.all(
        data.members.map(async (member: any) => {
          const userResponse = await fetch(`${BASE_URL}/users/id/${member.user_id}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          const userData = await userResponse.json();

          return {
            user_id: member.user_id,
            username: userData.username,
            role: member.role,
          };
        })
      );

      return membersWithInfo;
    } catch (error) {
      console.error('Error fetching group members:', error);
      setError('Erro ao carregar membros do grupo');
      return [];
    }
  };

  // Carregar mensagens do localStorage
  const loadMessagesFromStorage = (chatId: string, type: ChatType): Message[] => {
    const key = `conchat_messages_${type}_${chatId}`;
    const stored = localStorage.getItem(key);

    if (!stored) return [];

    try {
      return JSON.parse(stored);
    } catch (error) {
      console.error('Error loading messages:', error);
      return [];
    }
  };

  // Salvar mensagem no localStorage
  const saveMessageToStorage = (message: Message) => {
    const key = `conchat_messages_${message.type}_${message.chatId}`;
    const existing = loadMessagesFromStorage(message.chatId, message.type);

    const isDuplicate = existing.some((m: any) => m.uuid === message.uuid);
    if (isDuplicate) return;

    const updated = [...existing, message];
    const limited = updated.slice(-500);

    localStorage.setItem(key, JSON.stringify(limited));
  };

  // Atualizar status de mensagem
  const updateMessageStatus = (messageUuid: string, status: Message['status']) => {
    setMessages(prev =>
      prev.map(msg =>
        msg.uuid === messageUuid ? { ...msg, status } : msg
      )
    );

    if (chatParams) {
      const key = `conchat_messages_${chatParams.type}_${chatParams.chatId}`;
      const stored = loadMessagesFromStorage(chatParams.chatId, chatParams.type);
      const updated = stored.map(msg =>
        msg.uuid === messageUuid ? { ...msg, status } : msg
      );
      localStorage.setItem(key, JSON.stringify(updated));
    }
  };

  // Inicialização: carregar dados
  useEffect(() => {
    const init = async () => {
      setIsLoading(true);

      try {
        const user = await fetchCurrentUser();
        if (!user) throw new Error('Failed to load user');
        setCurrentUser(user);

        if (chatParams) {
          const msgs = loadMessagesFromStorage(chatParams.chatId, chatParams.type);
          setMessages(msgs);

          if (chatParams.type === 'group') {
            const members = await fetchGroupMembers(chatParams.chatId);
            setGroupMembers(members);
          }
        }

      } catch (err) {
        console.error('Init error:', err);
        setError('Erro ao carregar chat');
      } finally {
        setIsLoading(false);
      }
    };

    if (chatParams) {
      init();
    }
  }, [chatParams]);

  // Conectar MQTT
  useEffect(() => {
    if (!currentUser || !chatParams || mqttClient) return;

    const accessToken = localStorage.getItem('access_token');
    const username = currentUser.username;

    const client = mqtt.connect('ws://localhost:8083/mqtt', {
      username: username,
      password: accessToken || '',
      clientId: `conchat-${Math.random().toString(16).substring(2, 10)}`,
      reconnectPeriod: 5000,
      connectTimeout: 30000,
    });

    client.on('connect', () => {
      console.log('[MQTT] Connected to broker');
      setIsConnected(true);

      const topic = chatParams.type === 'dm'
        ? `/dms/${currentUser.uuid}`
        : `/groups/${chatParams.chatId}`;

      client.subscribe(topic, { qos: 1 }, (err) => {
        if (err) {
          console.error('Subscribe error:', err);
          setError('Erro ao inscrever no chat');
        } else {
          console.log('[MQTT] Subscribed to:', topic);
        }
      });
    });

    client.on('message', (_topic: string, payload: Buffer) => {
      try {
        const event: MqttEvent = JSON.parse(payload.toString());
        console.log('[MQTT] Message received:', event);

        if (event.type === 'MESSAGE_NEW') {
          const messageId = event.payload.message_id || uuidv4();

          // Verificar se a mensagem já existe (evita duplicação)
          setMessages(prev => {
            const messageExists = prev.some(msg => msg.uuid === messageId);

            if (messageExists) {
              // Se a mensagem já existe e é do usuário atual, atualizar status
              if (event.from === currentUser.uuid) {
                return prev.map(msg =>
                  msg.uuid === messageId ? { ...msg, status: 'delivered' as const } : msg
                );
              }
              // Mensagem já existe, não adicionar
              return prev;
            }

            // Mensagem nova, adicionar
            const newMessage: Message = {
              uuid: messageId,
              chatId: chatParams.chatId,
              type: chatParams.type,
              from: event.from,
              content: event.payload.content || '',
              timestamp: event.timestamp,
              status: 'delivered',
            };

            saveMessageToStorage(newMessage);
            return [...prev, newMessage];
          });
        }

      } catch (error) {
        console.error('Error parsing MQTT message:', error);
      }
    });

    client.on('error', (err: any) => {
      console.error('MQTT Error:', err);

      if (err.message?.includes('Not authorized') || err.code === 5) {
        setError('Sessão expirada. Faça login novamente.');
        setTimeout(() => {
          localStorage.clear();
          window.location.hash = '#login';
        }, 3000);
      } else {
        setError('Erro de conexão com servidor de mensagens');
      }
    });

    client.on('close', () => {
      console.log('[MQTT] Connection closed');
      setIsConnected(false);
    });

    client.on('offline', () => {
      console.log('[MQTT] Offline');
      setIsConnected(false);
      setError('Conexão perdida. Tentando reconectar...');
    });

    client.on('reconnect', () => {
      console.log('[MQTT] Reconnecting...');
      setError(null);
    });

    setMqttClient(client);

    return () => {
      client.end();
    };
  }, [currentUser, chatParams]);

  // Auto-scroll ao receber mensagens
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Enviar mensagem
  const sendMessage = () => {
    if (!inputText.trim() || !mqttClient || !currentUser || !chatParams) return;

    const sanitized = inputText.trim().substring(0, 2000);
    const messageUuid = uuidv4();
    const timestamp = new Date().toISOString();

    const newMessage: Message = {
      uuid: messageUuid,
      chatId: chatParams.chatId,
      type: chatParams.type,
      from: currentUser.uuid,
      content: sanitized,
      timestamp: timestamp,
      status: 'sending',
    };

    setMessages(prev => [...prev, newMessage]);
    saveMessageToStorage(newMessage);
    setInputText('');
    setIsSending(true);

    const event: MqttEvent = {
      type: 'MESSAGE_NEW',
      from: currentUser.uuid,
      payload: {
        message_id: messageUuid,
        content: newMessage.content,
      },
      timestamp: timestamp,
    };

    const topic = chatParams.type === 'dm'
      ? `/dms/${chatParams.chatId}`
      : `/groups/${chatParams.chatId}`;

    mqttClient.publish(topic, JSON.stringify(event), { qos: 1 }, (err) => {
      setIsSending(false);

      if (err) {
        console.error('[MQTT] Publish error:', err);
        updateMessageStatus(messageUuid, 'failed');
        setError('Erro ao enviar mensagem');
      } else {
        console.log('[MQTT] Message sent:', messageUuid);
        updateMessageStatus(messageUuid, 'sent');
      }
    });
  };

  // Funções auxiliares
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }
  };

  const getStatusIcon = (status: Message['status']): string => {
    switch (status) {
      case 'sending': return '○';
      case 'sent': return '✓';
      case 'delivered': return '✓✓';
      case 'read': return '✓✓';
      case 'failed': return '⚠';
      default: return '';
    }
  };

  const handleBack = () => {
    window.location.hash = '#chats';
  };

  const getImageUrl = (filename: string | undefined): string => {
    if (!filename) return '/default-avatar.png';
    return `${BASE_URL}/images/${filename}`;
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <button className="back-btn" onClick={handleBack}>←</button>

        {chatParams?.type === 'dm' ? (
          <div className="header-content">
            <img
              src={getImageUrl(chatParams.chatIcon)}
              alt="Avatar"
              className="header-avatar"
            />
            <div className="header-info">
              <h2 className="header-name">{chatParams.chatName}</h2>
              <span className="header-status">
                {isConnected ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        ) : (
          <div className="header-content">
            <div className="header-icon-wrapper">
              <img
                src={getImageUrl(chatParams?.chatIcon)}
                alt="Grupo"
                className="header-icon"
              />
            </div>
            <div className="header-info">
              <h2 className="header-name">{chatParams?.chatName}</h2>
              <span className="header-members">
                {groupMembers.map(m => m.username).join(', ')}
              </span>
            </div>
          </div>
        )}
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <p>{error}</p>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="messages-container" ref={messageListRef}>
        {isLoading ? (
          <div className="loading-spinner">
            <span className="spinner"></span>
            <p>Carregando mensagens...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-state">
            <p>Nenhuma mensagem ainda. Comece a conversa!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.uuid}
              className={`message ${msg.from === currentUser?.uuid ? 'message-own' : 'message-other'}`}
            >
              {chatParams?.type === 'group' && msg.from !== currentUser?.uuid && (
                <span className="message-sender">
                  {groupMembers.find(m => m.user_id === msg.from)?.username || 'Usuário'}
                </span>
              )}
              <div className="message-bubble">
                <p className="message-content">{msg.content}</p>
                <span className="message-time">
                  {formatTime(msg.timestamp)}
                  {msg.from === currentUser?.uuid && (
                    <span className={`message-status status-${msg.status}`}>
                      {getStatusIcon(msg.status)}
                    </span>
                  )}
                </span>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <footer className="chat-footer">
        <div className="input-container">
          <input
            type="text"
            className="message-input"
            placeholder="Digite sua mensagem..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            disabled={!isConnected || isSending}
            maxLength={2000}
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={!inputText.trim() || !isConnected || isSending}
            aria-label="Enviar mensagem"
          >
            {isSending ? <span className="spinner"></span> : '➤'}
          </button>
        </div>
      </footer>
    </div>
  );
}

export default Chat;
