import { useState, useEffect, useRef } from 'react';
import mqtt from 'mqtt';
import './ChatsList.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const MQTT_BROKER_URL = 'ws://localhost:8083/mqtt';
const CDN_BASE_URL = 'http://localhost:8000/api/v1/images/';

type MqttClient = ReturnType<typeof mqtt.connect>;

// ==================== INTERFACES ====================

interface CurrentUser {
  uuid: string;
  username: string;
  name: string;
  pfp_url?: string;
}

interface Friend {
  uuid: string;
  username: string;
  name: string;
  pfp_url?: string;
}

interface Group {
  uuid: string;
  name: string;
  icon_url?: string;
}

interface UserSearchResult {
  uuid: string;
  username: string;
  pfp_url?: string;
}

interface FriendRequest {
  requester_id: string;
  requester_username: string;
  requester_name: string;
  requester_pfp_url?: string;
  created_at: string;
}

interface MqttFriendEvent {
  type: 'FRIENDREQUEST_RECEIVED' | 'FRIENDSTATUS_UPDATE';
  from: string;
  payload: {
    requester_id?: string;
    requester_username?: string;
    requester_name?: string;
    requester_pfp_url?: string;
    action?: 'accept' | 'reject';
    user_id?: string;
    username?: string;
    name?: string;
    pfp_url?: string;
  };
  timestamp: string;
}

// ==================== COMPONENTE PRINCIPAL ====================

function ChatsList() {
  // Estado principal
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [activeTab, setActiveTab] = useState<'friends' | 'groups'>('friends');
  const [friends, setFriends] = useState<Friend[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);

  // Modais
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [showRequestsModal, setShowRequestsModal] = useState(false);

  // Busca
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Convites
  const [pendingRequests, setPendingRequests] = useState<FriendRequest[]>([]);
  const [requestsBadgeCount, setRequestsBadgeCount] = useState(0);

  // MQTT
  const [mqttClient, setMqttClient] = useState<MqttClient | undefined>(undefined);

  // Loading/Error
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ==================== FUNÇÕES AUXILIARES ====================

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const getImageUrl = (filename?: string) => {
    if (!filename) return undefined;
    return `${CDN_BASE_URL}${filename}`;
  };

  // ==================== FETCH DATA ====================

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        window.location.hash = '#login';
        return null;
      }

      // Buscar UUID do usuário
      const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!meResponse.ok) {
        if (meResponse.status === 401) {
          localStorage.clear();
          window.location.hash = '#login';
          return null;
        }
        throw new Error('Failed to fetch user ID');
      }

      const meData = await meResponse.json();
      const userId = meData.uuid;

      // Buscar dados completos do usuário
      const userResponse = await fetch(`${API_BASE_URL}/users/id/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!userResponse.ok) throw new Error('Failed to fetch user data');

      const userData = await userResponse.json();

      const user: CurrentUser = {
        uuid: userData.uuid,
        username: userData.username,
        name: userData.name,
        pfp_url: userData.pfp_url
      };

      setCurrentUser(user);
      return user;

    } catch (err) {
      console.error('Error fetching current user:', err);
      setError('Erro ao carregar dados do usuário');
      return null;
    }
  };

  const fetchFriends = async (userId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/friends`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch friends');

      const data = await response.json();
      const friendIds = data.friends || [];

      // Buscar dados completos de cada amigo
      const friendsData = await Promise.all(
        friendIds.map(async (friendObj: { id: string }) => {
          const friendResponse = await fetch(
            `${API_BASE_URL}/users/id/${friendObj.id}`,
            { headers: getAuthHeaders() }
          );

          if (!friendResponse.ok) return null;

          const friendData = await friendResponse.json();
          return {
            uuid: friendData.uuid,
            username: friendData.username,
            name: friendData.name,
            pfp_url: friendData.pfp_url
          };
        })
      );

      setFriends(friendsData.filter(f => f !== null) as Friend[]);

    } catch (err) {
      console.error('Error fetching friends:', err);
    }
  };

  const fetchGroups = async (userId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/groups`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch groups');

      const data = await response.json();
      const groupIds = data.groups || [];

      // Buscar dados completos de cada grupo
      const groupsData = await Promise.all(
        groupIds.map(async (groupObj: { id: string }) => {
          const groupResponse = await fetch(
            `${API_BASE_URL}/groups/${groupObj.id}`,
            { headers: getAuthHeaders() }
          );

          if (!groupResponse.ok) return null;

          const groupData = await groupResponse.json();
          return {
            uuid: groupData.uuid,
            name: groupData.name,
            icon_url: groupData.icon
          };
        })
      );

      setGroups(groupsData.filter(g => g !== null) as Group[]);

    } catch (err) {
      console.error('Error fetching groups:', err);
    }
  };

  const fetchPendingRequests = async (userId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${userId}/friends/requests/pending`,
        { headers: getAuthHeaders() }
      );

      if (!response.ok) throw new Error('Failed to fetch pending requests');

      const data = await response.json();
      const requests = data.requests || [];

      setPendingRequests(requests);
      setRequestsBadgeCount(requests.length);

    } catch (err) {
      console.error('Error fetching pending requests:', err);
    }
  };

  // ==================== MQTT ====================

  const connectMQTT = (user: CurrentUser) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const client = mqtt.connect(MQTT_BROKER_URL, {
        clientId: `web_${user.uuid}`,
        username: user.username,
        password: token,
        clean: false,
        keepalive: 60,
        reconnectPeriod: 1000
      });

      client.on('connect', () => {
        console.log('MQTT connected');

        // Subscrever ao tópico de notificações do usuário
        const topic = `/users/${user.uuid}`;
        client.subscribe(topic, { qos: 1 }, (err) => {
          if (err) {
            console.error('MQTT subscribe error:', err);
          } else {
            console.log(`Subscribed to ${topic}`);
          }
        });
      });

      client.on('message', (_topic: string, payload: Buffer) => {
        try {
          const event: MqttFriendEvent = JSON.parse(payload.toString());
          console.log('MQTT event received:', event);

          if (event.type === 'FRIENDREQUEST_RECEIVED') {
            // Novo convite de amizade recebido
            setRequestsBadgeCount(prev => prev + 1);
            setPendingRequests(prev => [...prev, {
              requester_id: event.payload.requester_id!,
              requester_username: event.payload.requester_username!,
              requester_name: event.payload.requester_name!,
              requester_pfp_url: event.payload.requester_pfp_url,
              created_at: event.timestamp
            }]);
          }

          if (event.type === 'FRIENDSTATUS_UPDATE') {
            if (event.payload.action === 'accept') {
              // Convite aceito - atualizar lista de amigos
              if (user) {
                fetchFriends(user.uuid);
              }
            }
          }

        } catch (err) {
          console.error('Error processing MQTT message:', err);
        }
      });

      client.on('error', (err) => {
        console.error('MQTT error:', err);
      });

      client.on('close', () => {
        console.log('MQTT disconnected');
      });

      setMqttClient(client);

    } catch (err) {
      console.error('Error connecting to MQTT:', err);
    }
  };

  // ==================== BUSCA DE USUÁRIOS ====================

  const searchUsers = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/users?q=${encodeURIComponent(query)}`,
        { headers: getAuthHeaders() }
      );

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setSearchResults(data.users || []);

    } catch (err) {
      console.error('Error searching users:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);

    // Debounce
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      searchUsers(value);
    }, 500);
  };

  // ==================== CONVITES DE AMIZADE ====================

  const sendFriendRequest = async (targetId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${targetId}/friends/request`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );

      const data = await response.json();

      if (response.ok) {
        alert('Convite enviado com sucesso!');
        setShowSearchModal(false);
        setSearchQuery('');
        setSearchResults([]);
      } else {
        alert(data.message || 'Erro ao enviar convite');
      }

    } catch (err) {
      console.error('Error sending friend request:', err);
      alert('Erro ao enviar convite');
    }
  };

  const respondToRequest = async (requesterId: string, action: 'accept' | 'reject') => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/users/${requesterId}/friends/request`,
        {
          method: 'PATCH',
          headers: getAuthHeaders(),
          body: JSON.stringify({ action })
        }
      );

      const data = await response.json();

      if (response.ok) {
        // Remover da lista de pendentes
        setPendingRequests(prev =>
          prev.filter(r => r.requester_id !== requesterId)
        );
        setRequestsBadgeCount(prev => Math.max(0, prev - 1));

        if (action === 'accept') {
          // Atualizar lista de amigos
          if (currentUser) {
            fetchFriends(currentUser.uuid);
          }
          alert('Convite aceito!');
        } else {
          alert('Convite recusado');
        }

      } else {
        alert(data.message || 'Erro ao responder convite');
      }

    } catch (err) {
      console.error('Error responding to friend request:', err);
      alert('Erro ao responder convite');
    }
  };

  // ==================== NAVEGAÇÃO ====================

  const openChat = (
    type: 'dm' | 'group',
    chatId: string,
    chatName: string,
    chatIcon?: string
  ) => {
    const params = new URLSearchParams({
      type,
      chatId,
      chatName,
      ...(chatIcon && { chatIcon })
    });

    window.location.hash = `chat?${params.toString()}`;
  };

  // ==================== EFFECTS ====================

  useEffect(() => {
    const initializeData = async () => {
      setIsLoading(true);

      const user = await fetchCurrentUser();
      if (!user) {
        setIsLoading(false);
        return;
      }

      await Promise.all([
        fetchFriends(user.uuid),
        fetchGroups(user.uuid),
        fetchPendingRequests(user.uuid)
      ]);

      connectMQTT(user);

      setIsLoading(false);
    };

    initializeData();

    return () => {
      if (mqttClient) {
        mqttClient.end();
      }
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // ==================== RENDER ====================

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p className="loading-text">Carregando...</p>
      </div>
    );
  }

  if (!currentUser) {
    return null;
  }

  return (
    <div className="chats-container">
      {/* Header */}
      <div className="chats-header">
        <div className="header-left">
          <img
            src={getImageUrl(currentUser.pfp_url) || 'https://via.placeholder.com/48'}
            alt={currentUser.name}
            className="header-user-avatar"
          />
          <div className="header-user-info">
            <h2>{currentUser.name}</h2>
            <p>@{currentUser.username}</p>
          </div>
        </div>
        <div className="header-right">
          <button
            className="header-btn"
            onClick={() => setShowSearchModal(true)}
          >
            + Adicionar Amigo
          </button>
          <button
            className="header-btn"
            onClick={() => setShowRequestsModal(true)}
          >
            Convites
            {requestsBadgeCount > 0 && (
              <span className="badge">{requestsBadgeCount}</span>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <span className="error-message">{error}</span>
          <button
            className="close-error-btn"
            onClick={() => setError(null)}
          >
            ×
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs-bar">
        <button
          className={`tab-btn ${activeTab === 'friends' ? 'active' : ''}`}
          onClick={() => setActiveTab('friends')}
        >
          Amigos
        </button>
        <button
          className={`tab-btn ${activeTab === 'groups' ? 'active' : ''}`}
          onClick={() => setActiveTab('groups')}
        >
          Grupos
        </button>
      </div>

      {/* Chats List */}
      <div className="chats-list">
        {activeTab === 'friends' ? (
          friends.length > 0 ? (
            friends.map(friend => (
              <div
                key={friend.uuid}
                className="chat-item"
                onClick={() => openChat('dm', friend.uuid, friend.name, friend.pfp_url)}
              >
                <img
                  src={getImageUrl(friend.pfp_url) || 'https://via.placeholder.com/52'}
                  alt={friend.name}
                  className="chat-item-avatar"
                />
                <div className="chat-item-info">
                  <p className="chat-item-name">{friend.name}</p>
                  <p className="chat-item-username">@{friend.username}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h3>Nenhum amigo ainda</h3>
              <p>Adicione amigos para começar a conversar!</p>
            </div>
          )
        ) : (
          groups.length > 0 ? (
            groups.map(group => (
              <div
                key={group.uuid}
                className="chat-item"
                onClick={() => openChat('group', group.uuid, group.name, group.icon_url)}
              >
                <img
                  src={getImageUrl(group.icon_url) || 'https://via.placeholder.com/52'}
                  alt={group.name}
                  className="chat-item-avatar"
                />
                <div className="chat-item-info">
                  <p className="chat-item-name">{group.name}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h3>Nenhum grupo ainda</h3>
              <p>Entre em grupos para conversar com várias pessoas!</p>
            </div>
          )
        )}
      </div>

      {/* Search Modal */}
      {showSearchModal && (
        <div className="modal-overlay" onClick={() => setShowSearchModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Buscar Usuários</h3>
              <button
                className="modal-close-btn"
                onClick={() => setShowSearchModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <input
                type="text"
                className="search-input"
                placeholder="Digite o nome ou username..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                autoFocus
              />

              {isSearching ? (
                <div className="search-empty">Buscando...</div>
              ) : searchResults.length > 0 ? (
                <div className="search-results">
                  {searchResults.map(user => (
                    <div key={user.uuid} className="search-result-item">
                      <div className="search-result-info">
                        <img
                          src={getImageUrl(user.pfp_url) || 'https://via.placeholder.com/40'}
                          alt={user.username}
                          className="search-result-avatar"
                        />
                        <span className="search-result-username">@{user.username}</span>
                      </div>
                      <button
                        className="add-friend-btn"
                        onClick={() => sendFriendRequest(user.uuid)}
                      >
                        Adicionar
                      </button>
                    </div>
                  ))}
                </div>
              ) : searchQuery.length >= 2 ? (
                <div className="search-empty">Nenhum usuário encontrado</div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Requests Modal */}
      {showRequestsModal && (
        <div className="modal-overlay" onClick={() => setShowRequestsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Convites de Amizade</h3>
              <button
                className="modal-close-btn"
                onClick={() => setShowRequestsModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {pendingRequests.length > 0 ? (
                pendingRequests.map(request => (
                  <div key={request.requester_id} className="request-item">
                    <div className="request-info">
                      <img
                        src={getImageUrl(request.requester_pfp_url) || 'https://via.placeholder.com/48'}
                        alt={request.requester_name}
                        className="request-avatar"
                      />
                      <div className="request-details">
                        <h4>{request.requester_name}</h4>
                        <p>@{request.requester_username}</p>
                      </div>
                    </div>
                    <div className="request-actions">
                      <button
                        className="accept-btn"
                        onClick={() => respondToRequest(request.requester_id, 'accept')}
                      >
                        Aceitar
                      </button>
                      <button
                        className="reject-btn"
                        onClick={() => respondToRequest(request.requester_id, 'reject')}
                      >
                        Recusar
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="search-empty">Nenhum convite pendente</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatsList;
