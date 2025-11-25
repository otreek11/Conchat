# Arquitetura

Esse documento busca esclarecer a arquitetura utilizada para o aplicativo Conchat, explicando e documentando tanto como funciona quanto justificando seu uso específico.

## Visão Geral

A arquitetura da aplicação se trata de uma hibridização entre as arquiteturas RESTful e Publish-Subscribe. 

- **RESTful:** Utilizada para autenticação e autorização em ações internas à aplicação, além de prover outras funcionalidades como a descoberta de novos usuários

- **Publish-Subscribe:** Utilizada para envio e recebimento de mensagens e eventos no geral (como pedidos de amizade ou convite para chat), a filosofia utilizada para a arquitetura portanto é orientada a eventos, já que cada mensagem pode ser dividida por eventos como "MESSAGE_NEW", "MESSAGE_READ", "FRIEND_INVITE" e etc.

# Arquitetura RESTful

A arquitetura RESTful foi utilizada para manusear as informações guardadas no sistema, como informações dos usuários, grupos e amizades definidas dentro do sistema. Ela também serve para realizar operações de autenticação/autorização dentro do sistema em geral.

Para ter acesso à API, a maior parte das requisições irão precisar de um token de acesso temporário, o `access_token`, também será necessário atualizar este token assim que ele expirar, para tal é necessário sempre manter-se o `refresh_token` (token de longa duração rotativo) guardado em memória no cliente, pois ele permite que seja gerado novos tokens temporários para acesso à API. Ambos os tokens podem ser gerados ao fazer login ou cadastro no sistema.

A URL base da API RESTful é: `https://api.conchat.com/v1`

A seguir contém-se os endpoints da API RESTful do sistema:
<!-- TODO -->

<!--

ESTRUTURA PADRÃO DE CADA MÉTODO

<details>
<summary><b>MÉTODO ENDPOINT</b> - DESC </summary>

- **Descrição:**
- **Parâmetros de Caminho:**
    - `name` (type, optional/required): desc
- **Parâmetros de Busca:**
    - `name` (type, optional/required): desc
- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` application/json
- **Body:**
    - `name` (type, optional/required): desc
- **Exemplo-Body:**
    ```json
    {
    
    }
    ```
- **Response:**
    - `name` (type): desc
- **Códigos:**
    - `code` title - desc
- **Exemplo-Response: [CODIGO]**
    ```json
    {
    
    }
    ```
- **Exemplo-Response: [CODIGO]**
    ```json
    {
    
    }
    ```
- **OBS.:**


</details>

-->

<details>
<summary><b>GET /ping</b> - Retorna 200 e horario atual </summary>

- **Descrição:** Envia uma requisição para o servidor apenas para checar se está ativo e retorna o horário em que recebeu a requisição.
- **Response:**
    - `received_at` (string): horário de recebimento da requisição
- **Códigos:**
    - `200` OK - Recebido
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "message": "Server is active",
        "received_at": "2025-11-21T17:35:20Z"
    }
    ```

</details>

## Endpoints de Autenticação

<details>
<summary><b>POST /auth/login</b> - Realizar login </summary>

- **Descrição:** Busca o usuário no sistema e retorna tokens
- **Headers:**
    - `Content-Type:` application/json
- **Body:**
    - `username` (string, required): o apelido público do usuário
    - `password` (string, required): a senha do usuário
- **Exemplo-Body:**
    ```json
    {
        "username": "example_username",
        "password": 123456789
    }
    ```
- **Response:**
    - `access_token` (string): token JWT temporário de acesso
    - `refresh_token` (string): token rotativo de longa duração
- **Códigos:**
    - `200` OK - Tokens retornados
    - `400` Bad Request - Campos obrigatórios não-especificados
    - `404` Not Found - Usuário não encontrado
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImV4YW1wbGVfdXNlcm5hbWUiLCJoZWxsbyI6ImJyZWF0aGUsIGJyZWF0aGUgaW4gdGhlIGFpci4gZG9udCBiZSBhZnJhaWQgdG8gY2FyZSIsImlhdCI6MTUxNjIzOTAyMn0.9Qwh0UDZT2viMPwVm_CCapQx4PKuK29QcUSVw2NFbFk",
        "refresh_token": "e1f27a57-19df-4d3e-9792-a32ec13400f3",
        "message": "Login sucessful"
    }
    ```
- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "User not found or wrong password"
    }
    ```


</details>

<details>
<summary><b>GET /auth/me</b> - Informações sobre usuário </summary>

- **Descrição:** Retorna informações sobre o próprio usuário dado o token
- **Headers:**
    - `Authorization:` Bearer `<token>`
- **Response:**
    - `uuid`: o identificador público do usuário
- **Códigos:**
    - `200` OK
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "uuid": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "message": "Retrieval sucessful"
    }
    ```

</details>

<details>
<summary><b>POST /auth/refresh</b> - Rotaciona tokens </summary>

- **Descrição:** Recebe o token rotativo, gera um novo token temporário e retorna um novo par de tokens (JWT e rotativo)
- **Headers:**
    - `Content-Type:` application/json
- **Body:**
    - `refresh_token` (string, required): o token rotativo
- **Exemplo-Body:**
    ```json
    {
        "refresh_token": "e1f27a57-19df-4d3e-9792-a32ec13400f3"
    }
    ```
- **Response:**
    - `access_token` (string): token JWT temporário de acesso
    - `refresh_token` (string): token rotativo de longa duração
- **Códigos:**
    - `200` OK - Tokens retornados
    - `400` Bad Request - Campo obrigatório não-especificado
    - `401` Unauthorized - Token rotativo expirado
    - `403` Forbidden - Token rotativo inválido
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImV4YW1wbGVfdXNlcm5hbWUiLCJyb3IyIjoiLi4uY29uIGxlbnRpdHVkIHBvZGVyb3NhIiwiaWF0IjoxNTE2MjM5MDIyfQ.qzc7N35y7WYyITs6MN2w2uL7jEvFsOzzQTHag2XvX64",
        "refresh_token": "e1f27a57-19df-4d3e-9792-a32ec13400f3",
        "message": "Login sucessful"
    }
    ```
- **Exemplo-Response: [401 Unauthorized]**
    ```json
    {
        "message": "Refresh token is expired"
    }
    ```
- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "Refresh token is invalid"
    }
    ```

</details>

## Endpoints de Usuário

<details>
<summary><b>GET /users</b> - Busca informação sobre vários usuários </summary>

- **Descrição:** Busca e retorna informações básicas sobre vários usuários de acordo com algum critério de busca 
- **Parâmetros de Busca:**
    - `q` (string, required): O nome não-único do usuário
    - `page` (number, optional): A página atual da busca (padrão é 1)
    - `limit` (number, optional): O limite de usuários por página (padrão é 20)
- **Headers:**
    - `Authorization:` Bearer `<token>`
- **Response:**
    - `users` (list): Uma lista contendo informações sobre os usuários encontrados, cada um contendo:
        - `username` (string): O apelido único do usuário
        - `uuid` (string): O id público do usuário
        - `pfp_url` (string): O caminho para a foto de perfil do usuário
- **Códigos:**
    - `200` OK - Usuários retornados com sucesso
    - `400` Bad Request - Requisição não contém `q` na URL
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "users": [
            {
                "username": "example_username",
                "uuid": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
                "pfp_url": "https://cdn.conchat.app/pfp/e7823sc6.webp"
            },
            {
                "username": "some_other_user",
                "uuid": "9ey2u37e-9d7s-2j34-ie9r-od9jksj2830s",
                "pfp_url": "https://cdn.conchatt.app/pfp/ue82yex.webp"
            }
        ],
        "message": "2 users found!"
    }
    ```
- **Exemplo-Response: [400 Bad Request]**
    ```json
    {
        "message": "Query parameter not specified!"
    }
    ```
- **OBS.:**
    - O código **200 OK** é retornado mesmo que a lista de usuários esteja vazia


</details>

<details>
<summary><b>POST /users</b> - Cria um usuário </summary>

- **Descrição:** Adiciona um novo usuário na base de dados do sistema
- **Headers:**
    - `Content-Type:` multipart/form-data
- **Body:**
    - `username` (string, required): o apelido único do usuário
    - `name` (string, required): o nome do usuário (não-único)
    - `email` (string, required): o email do usuário
    - `password` (string, required): a senha do usuário
    - `pfp` (file, optional): a foto de perfil do usuário (png, jpg, jpeg, webp)
- **Exemplo-Body:**
    ```
    ------SomeBoundary
    Content-Disposition: form-data; name="username"

    example_username
    ------SomeBoundary
    Content-Disposition: form-data; name="name"

    Nome de Exemplo
    ------SomeBoundary
    Content-Disposition: form-data; name="email"

    my@example.com
    ------SomeBoundary
    Content-Disposition: form-data; name="password"

    123456789
    ------SomeBoundary
    Content-Disposition: form-data; name="pfp"; filename="perfil.webp"
    Content-Type: image/webp

    (binary image content)
    ------SomeBoundary--

    ```
- **Response:**
    - `uuid` (string): o id público do usuário criado
    - `pfp_url` (string): a url do local onde a foto de perfil foi criada
    - `created_at` (string): o horário de criação do usuário
    - `access_token` (string): um token JWT de acesso de curta duração
    - `refresh_token` (string): um token de refrescamento do token de acesso de longa duração e rotativo
- **Códigos:**
    - `201` Created - Usuário criado com sucesso
    - `400` Bad Request - Erro de validação (Campo obrigatório não-preenchido ou inválido)
    - `409` Conflict - Já existe um usuário com o mesmo `username`
- **Exemplo-Response: [201 Created]**
    ```json
    {
        "uuid": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "pfp_url": "https://cdn.conchat.app/pfp/e7823sc6.webp",
        "created_at": "2025-11-21T17:35:20Z",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZTUyZGQ1OTItMmI0Mi00OGFlLWE5ZmQtOGM4ZTkzNzJiOTgyIiwiaGkiOiJ5b3UgYWN0dWFsbHkgZGVjb2RlZCB0aGlzLCB5b3UncmUgYSBjdXJpb3VzIG9uZSIsIm1lc3NhZ2VfdG9fdGhlX3dvcmxkIjoiYmUga2luZCwgd2UgYWxsIGRlc2VydmUgYSBsaXR0bGUgbG92ZSA6KSIsImV4cCI6MTcyOTU3MTcyMCwiaWF0IjoxNzI5NTcxMTIwfQ.0_z5gGK4tqktc-IuHX35c9BoCAy76L7f7NWWKbwi8FE",
        "refresh_token": "e1f27a57-19df-4d3e-9792-a32ec13400f3",
        "message": "User was created sucessfully"
    }
    ```
- **Exemplo-Response: [400 Bad Request]**
    ```json
    {
        "message": "'username' field must be provided!",
    }
    ```
- **Exemplo-Response: [409 Conflict]**
    ```json
    {
        "message": "Username 'example_username' is already taken",
    }
    ```
- **OBS.:**
    - `username` e `email` são campos únicos, e portanto não podem se repetir entre usuários


</details>

<details>
<summary><b>GET /users/{username}</b> - Busca informações de um usuário por apelido único</summary>

- **Descrição:** Busca um usuário na base de dados e retorna suas informações associadas
- **Parâmetros de Caminho:**
    - `username` (string, required): o apelido do usuário
- **Parâmetros de Busca:**
    - `fields` (list, optional): quais campos deseja-se retornar na resposta
- **Headers:**
    - `Authorization:` Bearer `<token>`
- **Response:**
    - `uuid` (string): o id público do usuário
    - `name` (string): o nome do usuário
    - `created_at` (string): a data de criação do usuário
    - `pfp_url` (string): o caminho para a foto de perfil do usuário
    - `email` (string): o email associado ao usuário
    - `n_friends` (number): a quantidade de amigos do usuário
- **Códigos:**
    - `200` OK - Usuário encontrado e informações retornadas
    - `404` Not Found - Usuário não está na base de dados
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "uuid": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "name": "Example Real Name",
        "created_at": "2025-11-21T17:35:20Z",
        "pfp_url": "https://cdn.conchat.app/pfp/e7823sc6.webp",
        "email": "my@example.com",
        "n_friends": 12,
        "message": "User example_username was found"
    }
    ```
- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Could not find user 'example_username2'"
    }
    ```
- **OBS.:**
    - Caso `fields` não seja especificado, retorna-se todos os campos


</details>

<details>
<summary><b>GET /users/id/{uuid}</b> - Busca informações de um usuário por UUID </summary>

- **Descrição:** Busca um usuário na base de dados e retorna suas informações associadas
- **Parâmetros de Caminho:**
    - `uuid` (string, required): o id público do usuário
- **Parâmetros de Busca:**
    - `fields` (list, optional): quais campos deseja-se retornar na resposta
- **Headers:**
    - `Authorization:` Bearer `<token>`
- **Response:**
    - `username` (string): o apelido único do usuário
    - `name` (string): o nome do usuário
    - `created_at` (string): a data de criação do usuário
    - `pfp_url` (string): o caminho para a foto de perfil do usuário
    - `email` (string): o email associado ao usuário
    - `n_friends` (number): a quantidade de amigos do usuário
- **Códigos:**
    - `200` OK - Usuário encontrado e informações retornadas
    - `404` Not Found - Usuário não está na base de dados
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "username": "example_username",
        "name": "Example Real Name",
        "created_at": "2025-11-21T17:35:20Z",
        "pfp_url": "https://cdn.conchat.app/pfp/e7823sc6.webp",
        "email": "my@example.com",
        "n_friends": 12,
        "message": "User example_username was found"
    }
    ```
- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Could not find user 'example_username2'"
    }
    ```
- **OBS.:**
    - Caso `fields` não seja especificado, retorna-se todos os campos


</details>

## Endpoints de Grupo

## WebHooks MQTT

O Broker EMQX utilizado para o sistema pub-sub permite a utilização de WebHooks para autorizar certas ações dentro do sistema, tais webhooks serão então implementados rodando um servidor Flask local (com URL base `http://127.0.0.1:5001/webhooks/v1`) para realizar as autorizações necessárias

<details>
<summary><b>POST /connect</b> - Autenticar JWT na conexão do EMQX</summary>

- **Descrição:** Recebe os dados da tentativa de conexão de um cliente MQTT e valida se o JWT enviado é válido. Retorna se o broker deve permitir ou negar a conexão.  
- **Headers:**
    - `Content-Type:` application/json
- **Body:**
    - `clientid` (string, required): ID do cliente MQTT
    - `username` (string, required): username do cliente
    - `password` (string, required): JWT do cliente
- **Exemplo-Body:**
    ```json
    {
        "clientid": "algum_id_de_cliente_aqui",
        "username": "user123",
        "password": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImV4YW1wbGVfdXNlcm5hbWUiLCJoZXkiOiJwbGF5IGRlbHRhcnVuZSwgaXRzIHF1aXRlIGEgZnVuIGdhbWUgeW91IGtub3cgOikiLCJpYXQiOjE1MTYyMzkwMjJ9.OV-DVy3HEEXracMkQlpgz8E4pYjkrv50pn2l0fjI3ZE"
    }
    ```
- **Response:**
    - `result` (string): `"allow"` ou `"deny"`
- **Códigos:**
    - `200` OK - Requisição processada com sucesso
    - `401` Unauthorized - JWT inválido ou expirado
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "result": "allow",
        "message": "Connection authorized"
    }
    ```
- **Exemplo-Response: [401 Unauthorized]**
    ```json
    {
        "result": "deny",
        "message": "JWT expired or invalid"
    }
    ```

</details>

<details>
<summary><b>POST /acl_auth</b> - Autorizar publicação/inscrição em tópico</summary>

- **Descrição:** Recebe a requisição do broker para autorizar um cliente a publicar/inscrever-se em um tópico MQTT específico.  
- **Headers:**
    - `Content-Type:` application/json
- **Body:**
    - `clientid` (string, required): ID do cliente MQTT
    - `username` (string, required): username do cliente
    - `password` (string, required): JWT do cliente
    - `topic` (string, required): tópico que o cliente quer publicar/inscrever
- **Exemplo-Body:**
    ```json
    {
        "clientid": "algum_id_de_cliente_aqui",
        "username": "user123",
        "password": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImV4YW1wbGVfdXNlcm5hbWUiLCJpdHNoYXJkIjoiaXRzIHJlYWxseSBoYXJkLCBpIGtub3csIHlldCB5b3UncmUgc3RpbGwgaGVyZSwgeW91IGhhdmVuJ3QgZ2l2ZW4gdXAiLCJpYXQiOjE1MTYyMzkwMjJ9.o2jd9AWDt1r_WU3WwF3xyX-cSo3qv1vVB05e9llmBR4",
        "topic": "/groups/uuid123",
    }
    ```
- **Response:**
    - `result` (string): `"allow"` ou `"deny"`
- **Códigos:**
    - `200` OK - Requisição processada
    - `401` Unauthorized - JWT invalido ou expirado
    - `403` Forbidden - Cliente não autorizado
- **Exemplo-Response: [200 OK]**
    ```json
    {
        "result": "allow",
        "message": "Authorized"
    }
    ```
- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "result": "deny",
        "message": "User not authorized in this topic"
    }
    ```

</details>

# Arquitetura Pub/Sub

A arquitetura Pub/Sub foi implementada para fins de comunicação entre clientes no app. Clientes publicam mensagens para o Broker utilizando o protocolo MQTT, e então o Broker repassa as mensagens para outros clientes inscritos naquele grupo.

O Broker utilizado no projeto foi o **EMQX**, sua escolha foi com base em uma análise intensa comparando os brokers Apache Kafka (Que apesar de não ser MQTT, ainda sim analisamos), Mosquitto e EMQX.

- **Apache Kafka:** O Kafka se demonstra extremamente forte em suas funcionalidades, e é de fato muito consistente e escalável, contudo seu overhead é muito elevado para uma aplicação mobile, além de que modificar permissões (quais clientes podem ler/enviar mensagens em quais grupos) pode se demonstrar uma tarefa de complexidade demasiadamente elevada.

- **Mosquitto:** O Broker Mosquitto é um broker muito simples que permite que facilmente seja implementado o protocolo MQTT para comunicação, contudo seu uso real para a aplicação seria complexo, já que ele apenas possui nativamente controle de permissão estático, sendo necessário ou reiniciar o broker a cada modificação de permissão (inviável) ou utilizar plugins que permitem que essas permissões sejam modificadas dinamicamente (complexo)

- **EMQX:** O Broker EMQX é ainda um broker MQTT relativamente simples de ser implementado, podendo ser utilizado ainda via Docker (facilita o deploy), e permite que implementemos nativamente a checagem de permissões definindo WebHooks para nosso backend cuidar da checagem, além de facilitar a mudança dessas permissões durante a execução do broker.

Após a análise, escolhemos utilizar o broker EMQX, por utilizar ainda o protocolo MQTT (o que é mais eficiente para uma aplicação mobile) e possuir a maioria das funcionalidades que são necessárias para a construção do aplicativo.

Tal arquitetura ainda permite (caso haja necessidade para uma maior robustez/escalabilidade) integrarmos o EMQX com o Kafka, onde os usuários enviam mensagens para o broker EMQX (eficiente) e o broker envia para o Kafka (escalável), permitindo a adição de replicação global com facilidade, o que facilita a aplicação a ser escalável geograficamente.

A URL base para conexão com o broker EMQX é: `wss://broker.conchat.com/mqtt`

Os eventos devem conter todas as informações necessárias para serem processados automaticamente pelo cliente, e sua estrutura deve ser um JSON contendo:

- `type`: o tipo de evento
- `from`: o usuário que causou o evento
- `payload`: um json do conteúdo específico do evento
- `timestamp`: o horário de envio do evento

Aqui estão especificados os tópicos dentro do sistema:

<!-- 

<details>
<summary><b>TOPIC</b> - DESC</summary>

- **Descrição:**
- **PUBLISH-able:**
- **SUBSCRIBE-able:**
- **Eventos Possiveis:** 
- **Payload Base:**

</details>

-->

<details>
<summary><b>/groups/{group_uuid}</b> - Mensageria em grupo</summary>

- **Descrição:** Tópico para eventos relativos ao grupo {grupo_uuid}
- **PUBLISH-able:** Apenas quem pertence ao grupo
- **SUBSCRIBE-able:** Apenas quem pertence ao grupo
- **Eventos Possiveis:**
    - `MESSAGE_NEW`: mensagem nova recebida
    - `MESSAGE_EDIT`: mensagem sendo editada
    - `MESSAGE_DELETED`: mensagem apagada
    - `MESSAGE_DELIVERED`: mensagem recebida
    - `MESSAGE_READ`: mensagem lida
    - `GROUPMEMBER_ADD`: adição de novo membro
    - `GROUPMEMBER_REMOVE`: remoção de membro
    - `GROUPMEMBER_ROLEEDIT`: edição das permissões de um membro
    - `GROUPDATA_UPDATE`: indica uma mudança em informações sobre o grupo (nome, imagem, ...)
</details>

<details>
<summary><b>/dms/{user_uuid}</b> - Mensageria privada</summary>

- **Descrição:** Tópico para eventos relativos a mensageria privada
- **PUBLISH-able:** Apenas por usuários com amizade com o usuário {user_uuid}
- **SUBSCRIBE-able:** Apenas pelo próprio usuário especificado em {user_uuid}
- **Eventos Possiveis:**
    - `MESSAGE_NEW`: mensagem nova recebida
    - `MESSAGE_EDIT`: mensagem sendo editada
    - `MESSAGE_DELETED`: mensagem apagada
    - `MESSAGE_DELIVERED`: mensagem recebida
    - `MESSAGE_READ`: mensagem lida
</details>

<details>
<summary><b>/users/{user_uuid}</b> - Eventos do usuário</summary>

- **Descrição:** Tópico para eventos relativos a eventos relativos ao usuário
- **PUBLISH-able:** Apenas pelo próprio sistema
- **SUBSCRIBE-able:** Apenas pelo próprio usuário especificado em {user_uuid}
- **Eventos Possiveis:**
    - `FRIENDREQUEST_RECEIVED`: solicitação de amizade recebida
    - `FRIENDSTATUS_UPDATE`: uma atualização sobre a relação entre usuários
- **OBS.:**
    - `FRIENDSTATUS_UPDATE` nunca indica que uma solicitação foi rejeitada, apenas se foi aceita ou se o usuário foi bloqueado
</details>