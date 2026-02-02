# Setup do EMQX no Conchat

## Visão Geral

O broker EMQX implementa a arquitetura Pub/Sub do Conchat, permitindo comunicação em tempo real via MQTT sobre WebSocket Secure (WSS).

### Arquitetura

```
[Cliente Mobile]
    ↓ WSS (wss://broker.conchat.com:8084)
[EMQX Broker :8084, :18083]
    ↓ HTTP Auth/AuthZ
[Webhooks Server :5001]
    ↓ Validação JWT + Queries DB
[Backend :8000] ← Compartilha DB + SECRET_KEY
```

## Componentes

### 1. EMQX Broker
- **Versão**: Open Source 5.8.3
- **Portas**:
  - 8084: WebSocket Secure (WSS) - produção
  - 8083: WebSocket (WS) - desenvolvimento
  - 18083: Dashboard web (admin:public)
- **Persistência**: Volume Docker `emqx-data`

### 2. Webhooks Server
- **Porta**: 5001 (não expor publicamente em produção!)
- **Endpoints**:
  - `POST /webhooks/v1/connect` - Autenticação JWT
  - `POST /webhooks/v1/acl_auth` - Autorização ACL
  - `GET /webhooks/v1/ping` - Health check

### 3. Regras de Autorização

#### Tópico `/groups/{group_uuid}`
- **PUBLISH/SUBSCRIBE**: Apenas membros do grupo (UserGroup no DB)

#### Tópico `/dms/{user_uuid}`
- **SUBSCRIBE**: Apenas o próprio user_uuid
- **PUBLISH**: Apenas amigos com Friendship.status == APPROVED

#### Tópico `/users/{user_uuid}`
- **SUBSCRIBE**: Apenas o próprio user_uuid
- **PUBLISH**: Negado (apenas sistema)

## Como Iniciar

### Primeira Execução

Os certificados SSL já foram gerados automaticamente durante a implementação. Se precisar regerá-los:

```bash
cd emqx/ssl
openssl genrsa -out key.pem 2048
MSYS_NO_PATHCONV=1 openssl req -new -x509 -key key.pem -out cert.pem -days 365 \
  -subj "/C=BR/ST=State/L=City/O=Conchat/CN=localhost"
```

### Subir os Containers

```bash
cd c:\Users\User\OneDrive\Documentos\GitHub\Conchat
docker-compose up --build
```

Para rodar em background:
```bash
docker-compose up -d --build
```

### Verificar Status

```bash
docker-compose ps
# Esperado: backend (Up), webhooks (Up), emqx (Up, healthy)
```

### Acessar Dashboard EMQX

1. Abrir navegador: http://localhost:18083
2. Login: `admin` / `public`
3. Explorar:
   - **Overview**: Métricas gerais do broker
   - **Clients**: Conexões ativas
   - **Subscriptions**: Tópicos subscritos
   - **Authentication**: Configuração HTTP Auth
   - **Authorization**: Configuração HTTP AuthZ

## Conexão Cliente MQTT

### Exemplo JavaScript (Node.js)

```javascript
import mqtt from 'mqtt';

const client = mqtt.connect('wss://localhost:8084/mqtt', {
  username: 'seu_username',
  password: 'SEU_JWT_TOKEN_AQUI',  // JWT do /auth/login
  clientId: `conchat-${Math.random().toString(16).substr(2, 8)}`,
  rejectUnauthorized: false,  // Para certificado self-signed em dev
});

client.on('connect', () => {
  console.log('✓ Conectado ao EMQX');

  // Subscribe ao tópico de usuário
  client.subscribe('/users/SEU_USER_UUID', (err) => {
    if (err) console.error('✗ Erro ao subscribir:', err);
    else console.log('✓ Subscrito ao tópico');
  });
});

client.on('message', (topic, message) => {
  const event = JSON.parse(message.toString());
  console.log(`Evento recebido em ${topic}:`, event);
});

client.on('error', (error) => {
  console.error('✗ Erro:', error);
});
```

### Exemplo Python (paho-mqtt)

```python
import paho.mqtt.client as mqtt
import json

JWT_TOKEN = "SEU_JWT_AQUI"
USER_UUID = "SEU_USER_UUID"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Conectado ao EMQX")
        client.subscribe(f"/users/{USER_UUID}")
    else:
        print(f"✗ Falha. Código: {rc}")

def on_message(client, userdata, msg):
    event = json.loads(msg.payload.decode())
    print(f"Evento em {msg.topic}: {event}")

client = mqtt.Client(client_id="conchat-py")
client.username_pw_set("username", JWT_TOKEN)
client.tls_set()
client.tls_insecure_set(True)  # Dev only!

client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 8084, 60)
client.loop_forever()
```

## Testes

### 1. Health Checks

```bash
# Backend
curl http://localhost:8000/api/v1/ping

# Webhooks
curl http://localhost:5001/webhooks/v1/ping

# EMQX Dashboard
# Navegador: http://localhost:18083
```

### 2. Testar Autenticação

```bash
# Criar usuário
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mqtttest",
    "name": "Test User",
    "email": "mqtt@test.com",
    "password": "testpass123"
  }'

# Fazer login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "mqtttest", "password": "testpass123"}'

# Copiar o access_token

# Testar webhook de conexão
curl -X POST http://localhost:5001/webhooks/v1/connect \
  -H "Content-Type: application/json" \
  -d '{
    "clientid": "test-123",
    "username": "mqtttest",
    "password": "SEU_JWT_AQUI"
  }'

# Esperado: {"result": "allow"}
```

### 3. Testar Autorização ACL

```bash
# Subscribe ao próprio tópico (DEVE PERMITIR)
curl -X POST http://localhost:5001/webhooks/v1/acl_auth \
  -H "Content-Type: application/json" \
  -d '{
    "clientid": "test-123",
    "username": "mqtttest",
    "password": "SEU_JWT_AQUI",
    "topic": "/users/SEU_USER_UUID",
    "action": "subscribe"
  }'

# Esperado: {"result": "allow"}

# Publish ao tópico de usuário (DEVE NEGAR)
curl -X POST http://localhost:5001/webhooks/v1/acl_auth \
  -H "Content-Type: application/json" \
  -d '{
    "clientid": "test-123",
    "username": "mqtttest",
    "password": "SEU_JWT_AQUI",
    "topic": "/users/SEU_USER_UUID",
    "action": "publish"
  }'

# Esperado: {"result": "deny", "message": "Only system can publish to user topics"}
```

## Troubleshooting

### "Connection refused" ao conectar EMQX
- **Causa**: Containers não estão rodando
- **Solução**: `docker-compose ps` - todos devem estar "Up"

### "JWT expired or invalid"
- **Causa**: SECRET_KEY diferente entre backend e webhooks
- **Solução**: Verificar que [backend/.env](../backend/.env) e [webhooks/.env](../webhooks/.env) têm mesmo SECRET_KEY

### "User not authorized in this topic"
- **Causa**: Regras ACL ou dados no banco
- **Solução**: Verificar UserGroup/Friendship no banco de dados

### Webhooks não acessa banco
- **Causa**: Volume não compartilhado
- **Solução**: Verificar volume `backend-db` montado em ambos os serviços

### EMQX não chama webhooks
- **Causa**: Rede Docker incorreta
- **Solução**: Todos devem estar em `conchat-network`

### "SSL handshake failed"
- **Causa**: Certificados ausentes/inválidos
- **Solução**: Verificar [emqx/ssl/](../emqx/ssl/) com `cert.pem` e `key.pem`

### Ver logs

```bash
# Logs do backend
docker-compose logs -f backend

# Logs dos webhooks
docker-compose logs -f webhooks

# Logs do EMQX
docker-compose logs -f emqx

# Logs de todos
docker-compose logs -f
```

## Segurança

### Checklist de Desenvolvimento
- ✅ Certificados self-signed OK
- ✅ Dashboard com senha padrão OK
- ✅ Porta 5001 exposta OK (para testes)
- ✅ SECRET_KEY compartilhado
- ✅ SQLite compartilhado via volume

### Checklist de Produção
- [ ] **CRÍTICO**: Certificados SSL válidos (Let's Encrypt)
- [ ] **CRÍTICO**: Mudar senha do dashboard EMQX
- [ ] **CRÍTICO**: NÃO expor porta 5001 publicamente
- [ ] SECRET_KEY forte e único
- [ ] Migrar para PostgreSQL/MySQL
- [ ] Configurar rate limiting no EMQX
- [ ] Firewall: apenas 8084 e 18083 (se necessário)
- [ ] HTTPS para dashboard via reverse proxy
- [ ] Backups automatizados
- [ ] Monitoramento (Prometheus/Grafana)
- [ ] Logs centralizados

### Rate Limiting (Produção)

Adicionar ao [emqx.conf](../emqx/etc/emqx.conf):

```conf
limiter {
  connection {
    rate = "1000/s"
    capacity = 1000
  }

  message_in {
    rate = "100/s"
    capacity = 100
  }
}
```

## Estrutura de Eventos MQTT

Todos os eventos seguem o formato:

```json
{
  "type": "MESSAGE_NEW",
  "from": "user_uuid_que_causou",
  "payload": {
    "message_id": "...",
    "content": "...",
    ...
  },
  "timestamp": "2025-11-21T17:35:20Z"
}
```

### Tipos de Eventos

#### Em `/groups/{group_uuid}`:
- `MESSAGE_NEW`, `MESSAGE_EDIT`, `MESSAGE_DELETED`
- `MESSAGE_DELIVERED`, `MESSAGE_READ`
- `GROUPMEMBER_ADD`, `GROUPMEMBER_REMOVE`, `GROUPMEMBER_ROLEEDIT`
- `GROUPDATA_UPDATE`

#### Em `/dms/{user_uuid}`:
- `MESSAGE_NEW`, `MESSAGE_EDIT`, `MESSAGE_DELETED`
- `MESSAGE_DELIVERED`, `MESSAGE_READ`

#### Em `/users/{user_uuid}`:
- `FRIENDREQUEST_RECEIVED`
- `FRIENDSTATUS_UPDATE`

## Monitoramento

### Métricas Importantes (Dashboard)
- **Connections**: Conexões ativas
- **Messages/sec**: Taxa de mensagens
- **Subscriptions**: Total de inscrições
- **Topics**: Tópicos ativos

### Alertas Recomendados
- Taxa de conexões falhadas > 10%
- Taxa de autorização negada > 20%
- CPU/Memória do EMQX > 80%
- Latência webhooks > 500ms

## Melhorias Futuras

1. **PostgreSQL**: Migrar de SQLite para produção
2. **Redis**: Cache para validações JWT e permissões
3. **Kafka**: Integração para escalabilidade global
4. **Métricas**: Prometheus + Grafana
5. **CI/CD**: Pipeline automatizado
6. **Testes**: Suite automatizada
7. **Rate Limiting**: Granular por usuário/grupo

## Referências

- [EMQX 5.x Documentation](https://docs.emqx.com/en/emqx/v5.0/)
- [MQTT Protocol](https://mqtt.org/)
- [Arquitetura Conchat](./Arquitetura.md)
- [Plano de Implementação](../.claude/plans/twinkling-noodling-manatee.md)
