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

<details>
<summary><b>DELETE /users/{id}</b> - Remove um usuário do sistema</summary>

- **Descrição:**  Remove permanentemente um usuário identificado pelo seu `id`. Apenas usuários autorizados (administradores e o próprio usuário) podem executar esta operação.

- **Parâmetros de Caminho:**
    - `id` (string, **required**): Identificador único do usuário a ser removido.

- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` application/json

- **Response:**
    - `message` (string): Mensagem informando o resultado da operação.

- **Códigos:**
    - `200` OK – Usuário removido com sucesso  
    - `401` Unauthorized – Token ausente, inválido ou expirado  
    - `403` Forbidden – Usuário autenticado não possui permissão para esta ação  
    - `404` Not Found – Usuário não encontrado  
    - `500` Internal Server Error – Erro interno ao tentar remover o usuário  

- **Exemplo-Response: [200]**
    ```json
    {
      "message": "User removed"
    }
    ```

- **Exemplo-Response: [404]**
    ```json
    {
      "message": "User not found"
    }
    ```

</details>

<details>
<summary><b>PATCH /users/{id}</b> - Atualiza dados de um usuário</summary>

- **Descrição:** Atualiza parcialmente os dados de um usuário identificado pelo seu `id`. Apenas o próprio usuário ou um administrador podem executar esta operação.

- **Parâmetros de Caminho:**
    - `id` (string, **required**): Identificador único do usuário a ser atualizado.

- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` multipart/form-data

- **Body:** 
    - `username` (string, optional): Novo nome de usuário.  
    - `name` (string, optional): Novo nome completo.  
    - `email` (string, optional): Novo e-mail.  
    - `password` (string, optional): Nova senha (mínimo 8 caracteres).  
    - `pfp` (file, optional): Nova foto de perfil (imagem).

- **Exemplo-Body:** 
    ```
    username=new_username
    name=Novo Nome
    email=novo@email.com
    password=nova_senha_segura
    pfp=@foto.png
    ```

- **Response:**
    - `uuid` (string): Identificador do usuário.
    - `pfp_url` (string, nullable): URL da nova foto de perfil.  
    - `message` (string): Mensagem informando o resultado da operação.

- **Códigos:**
    - `200` OK – Usuário atualizado com sucesso  
    - `400` Bad Request – Dados inválidos ou nenhum campo enviado  
    - `401` Unauthorized – Token ausente, inválido ou expirado  
    - `403` Forbidden – Usuário autenticado não possui permissão para esta ação  
    - `404` Not Found – Usuário não encontrado  
    - `409` Conflict – Username ou email já em uso  
    - `500` Internal Server Error – Erro interno ao tentar atualizar o usuário  

- **Exemplo-Response: [200]**
    ```json
    {
      "uuid": "a1b2c3d4-e5f6-7890-abcd-1234567890ef",
      "pfp_url": "https://cdn.conchat.com/foto12342143412.png",
      "message": "User updated successfully"
    }
    ```

- **Exemplo-Response: [404]**
    ```json
    {
      "message": "User not found"
    }
    ```

- **Exemplo-Response: [403]**
    ```json
    {
      "message": "Forbidden"
    }
    ```

- **OBS.:**
    - Apenas o **próprio usuário** ou um **administrador** pode atualizar os dados.
    - É possível enviar apenas os campos que deseja alterar.
    - Campos presentes com `null` serão apagados (caso possivel), campos ausentes não serão modificados
    - Caso `username` ou `email` já estejam em uso, a operação será rejeitada com `409 Conflict`.
    - Se nenhum campo válido for enviado, a API retornará `400 Bad Request`.
    - O campo `pfp` aceita apenas arquivos permitidos conforme as regras do backend (`allowed_file`).

</details>

## Endpoints de Grupo

<details>
<summary><b>POST /groups</b> - Cria um grupo </summary>

- **Descrição:** Cria um novo grupo no sistema e registra o usuário autenticado como criador do grupo
- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` multipart/form-data
- **Body:**
    - `name` (string, required): o nome do grupo
    - `icon` (file, optional): o ícone do grupo (png, jpg, jpeg, webp)
- **Exemplo-Body:**
    ```
    ------SomeBoundary
    Content-Disposition: form-data; name="name"

    Amigos
    ------SomeBoundary
    Content-Disposition: form-data; name="icon"; filename="grupo.webp"
    Content-Type: image/webp

    (binary image content)
    ------SomeBoundary--

    ```
- **Response:**
    - `uuid` (string): o id público do grupo criado
    - `name` (string): o nome do grupo
    - `icon_url` (string): a url do local onde o ícone do grupo foi salvo
    - `registered_at` (string): o horário de criação do grupo
    - `message` (string): mensagem de confirmação
- **Códigos:**
    - `201` Created - Grupo criado com sucesso
    - `400` Bad Request - Erro de validação (Campo obrigatório não-preenchido ou inválido)
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado
- **Exemplo-Response: [201 Created]**
    ```json
    {
        "uuid": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "name": "Amigos",
        "icon_url": "https://cdn.conchat.app/groups/icons/9s82ks7d.webp",
        "registered_at": "2026-01-14T22:41:32Z",
        "message": "Group was created successfully"
    }
    ```
- **Exemplo-Response: [400 Bad Request]**
    ```json
    {
        "message": "'name' field must be provided!"
    }
    ```
- **Exemplo-Response: [401 Unauthorized]**
    ```json
    {
        "message": "Unauthorized"
    }
    ```
- **OBS.:**
    - O campo `name` é obrigatório e não pode ser vazio
    - O campo `icon` é opcional e aceita apenas arquivos de imagem (`png`, `jpg`, `jpeg`, `webp`)
    - O campo `registered_at` é definido automaticamente pelo servidor no momento da criação
    - O usuário autenticado que cria o grupo pode ser automaticamente associado como membro/administrador do grupo

</details>

<details>
<summary><b>DELETE /groups/{id}</b> - Remove um grupo </summary>

- **Descrição:** Remove permanentemente um grupo do sistema. Apenas o criador do grupo ou um usuário com permissão administrativa pode executar esta operação.

- **Headers:**
    - `Authorization:` Bearer `<token>`

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único (UUID) do grupo a ser removido

- **Response:**
    - `message` (string): mensagem informando o resultado da operação

- **Códigos:**
    - `200` OK - Grupo removido com sucesso  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário autenticado não possui permissão para deletar este grupo  
    - `404` Not Found - Grupo não encontrado  
    - `500` Internal Server Error - Erro interno ao tentar remover o grupo  

- **Exemplo-Response: [200 OK]**
    ```json
    {
        "message": "Group was deleted successfully"
    }
    ```

- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Group not found"
    }
    ```

- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "Forbidden"
    }
    ```

- **OBS.:**
    - Apenas o **criador do grupo** ou um **administrador** pode deletar o grupo.
    - A exclusão do grupo remove automaticamente todas as relações de membros associadas (`cascade`).
    - Caso o grupo possua um ícone salvo, o arquivo poderá ser removido do sistema após a exclusão.
    - A operação é **irreversível**.

</details>

<details>
<summary><b>PATCH /groups/{id}</b> - Atualiza dados de um grupo </summary>

- **Descrição:** Atualiza parcialmente os dados de um grupo identificado pelo seu `id`. Apenas o **criador do grupo (owner)** ou um **administrador** podem executar esta operação.

- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` multipart/form-data

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único do grupo

- **Body:**
    - `name` (string, optional): novo nome do grupo  
    - `icon` (file, optional): novo ícone do grupo (`png`, `jpg`, `jpeg`, `webp`)  

- **Exemplo-Body:**
    ```
    ------SomeBoundary
    Content-Disposition: form-data; name="name"

    Novo Nome do Grupo
    ------SomeBoundary
    Content-Disposition: form-data; name="icon"; filename="novo_icone.webp"
    Content-Type: image/webp

    (binary image content)
    ------SomeBoundary--
    ```

- **Response:**
    - `uuid` (string): o id público do grupo
    - `name` (string): o nome atualizado do grupo
    - `icon_url` (string, nullable): a url do novo ícone do grupo
    - `message` (string): mensagem informando o resultado da operação

- **Códigos:**
    - `200` OK - Grupo atualizado com sucesso  
    - `400` Bad Request - Nenhum campo válido enviado ou dados inválidos  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário não é o criador do grupo nem administrador  
    - `404` Not Found - Grupo não encontrado  
    - `500` Internal Server Error - Erro interno ao tentar atualizar o grupo  

- **Exemplo-Response: [200 OK]**
    ```json
    {
        "uuid": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "name": "Novo Nome do Grupo",
        "icon_url": "https://cdn.conchat.app/groups/icons/9s82ks7d.webp",
        "message": "Group was updated successfully"
    }
    ```

- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Group not found"
    }
    ```

- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "Forbidden"
    }
    ```

- **OBS.:**
    - Apenas o **criador do grupo (owner)** ou um **administrador** pode atualizar os dados.
    - É possível enviar apenas os campos que deseja alterar.
    - Se nenhum campo válido for enviado, a API retornará `400 Bad Request`.
    - O campo `icon` aceita apenas arquivos permitidos conforme as regras do backend (`allowed_file`).
    - Caso um novo ícone seja enviado, o ícone antigo poderá ser removido do sistema após a atualização.

</details>

<details>
<summary><b>POST /groups/{id}/members</b> - Adiciona um membro ao grupo </summary>

- **Descrição:** Adiciona um usuário a um grupo existente. Apenas o **criador do grupo (owner)** ou um **administrador** pode executar esta operação.

- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` application/json

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único do grupo

- **Body:**
    - `user_id` (string, required): o identificador do usuário que será adicionado ao grupo
    - `role` (string, optional): papel do usuário no grupo (`member`, `admin`)  
      - Valor padrão: `member`

- **Exemplo-Body:**
    ```json
    {
        "user_id": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "role": "member"
    }
    ```

- **Response:**
    - `group_id` (string): o id do grupo
    - `user_id` (string): o id do usuário adicionado
    - `role` (string): papel atribuído ao usuário
    - `message` (string): mensagem de confirmação

- **Códigos:**
    - `201` Created - Usuário adicionado ao grupo com sucesso  
    - `400` Bad Request - Campo obrigatório ausente ou inválido  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário não é o criador do grupo nem administrador  
    - `404` Not Found - Grupo ou usuário não encontrado  
    - `409` Conflict - Usuário já é membro do grupo  
    - `500` Internal Server Error - Erro interno ao tentar adicionar o usuário  

- **Exemplo-Response: [201 Created]**
    ```json
    {
        "group_id": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "user_id": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "role": "member",
        "message": "User was added to group successfully"
    }
    ```

- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Group not found"
    }
    ```

- **Exemplo-Response: [409 Conflict]**
    ```json
    {
        "message": "User is already a member of this group"
    }
    ```

- **OBS.:**
    - Apenas o **criador do grupo (owner)** ou um **administrador** pode adicionar novos membros.
    - O campo `role` é opcional e, se não informado, o usuário será adicionado como `member`.
    - Um usuário não pode ser adicionado ao mesmo grupo mais de uma vez.
    - O backend deve validar se o usuário informado existe antes de criar o vínculo.

</details>

<details>
<summary><b>GET /groups/{id}/members</b> - Lista os membros de um grupo</summary>

- **Descrição:** Retorna a lista de todos os usuários pertencentes a um grupo, incluindo seus papéis (`role`) dentro dele.

- **Regras de Permissão:**  
    - O **owner** pode listar todos os membros  
    - O **admin** pode listar todos os membros  
    - Um **member** pode listar todos os membros  
    - Usuários que **não pertencem ao grupo** não podem acessar este recurso  

- **Headers:**
    - `Authorization:` Bearer `<token>`

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único do grupo  

- **Query Params (opcional):**
    - `role` (string, optional): filtra membros por papel  
        - Valores aceitos: `owner`, `admin`, `member`  

- **Response:**
    - `group_id` (string): o id do grupo  
    - `members` (array): lista de membros do grupo  
        - `user_id` (string): id do usuário  
        - `role` (string): papel do usuário no grupo  

- **Códigos:**
    - `200` OK - Lista de membros retornada com sucesso  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário autenticado não pertence ao grupo  
    - `404` Not Found - Grupo não encontrado  
    - `500` Internal Server Error - Erro interno ao buscar os membros  

- **Exemplo-Response: [200 OK]**
    ```json
    {
        "group_id": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "members": [
            {
                "user_id": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
                "role": "owner"
            },
            {
                "user_id": "a7f2b3c1-9d8e-4c4f-9b7a-3c12f54eab10",
                "role": "admin"
            },
            {
                "user_id": "b92a1c43-2f6d-4b89-90f3-8a1c92de11aa",
                "role": "member"
            }
        ]
    }
    ```

- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "You are not a member of this group"
    }
    ```

- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "Group not found"
    }
    ```

- **OBS.:**
    - Apenas usuários que **pertencem ao grupo** podem listar seus membros.
    - O papel (`role`) indica o nível de permissão do usuário dentro do grupo.
    - O resultado pode ser filtrado por papel usando o parâmetro `role`.
    - Este endpoint **não expõe dados sensíveis do usuário**, apenas identificador e papel no grupo.

</details>

<details>
<summary><b>DELETE /groups/{id}/members/{user_id}</b> - Remove um membro do grupo </summary>

- **Descrição:** Remove um usuário de um grupo específico. Apenas o **criador do grupo (owner)** ou um **administrador** podem executar esta operação.

- **Headers:**
    - `Authorization:` Bearer `<token>`

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único do grupo  
    - `user_id` (string, required): o identificador do usuário a ser removido do grupo  

- **Body:**  
    - Nenhum

- **Response:**
    - `group_id` (string): o id do grupo  
    - `user_id` (string): o id do usuário removido  
    - `message` (string): mensagem informando o resultado da operação  

- **Códigos:**
    - `200` OK - Usuário removido do grupo com sucesso  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário não é o criador do grupo nem administrador  
    - `404` Not Found - Grupo ou usuário não encontrado, ou usuário não pertence ao grupo  
    - `500` Internal Server Error - Erro interno ao tentar remover o membro  

- **Exemplo-Response: [200 OK]**
    ```json
    {
        "group_id": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "user_id": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "message": "User was removed from group successfully"
    }
    ```

- **Exemplo-Response: [404 Not Found]**
    ```json
    {
        "message": "User is not a member of this group"
    }
    ```

- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "Forbidden"
    }
    ```

- **OBS.:**
    - Apenas o **criador do grupo (owner)** ou um **administrador** pode remover membros.
    - Não é possível remover um usuário que não esteja associado ao grupo.
    - A remoção apaga apenas o vínculo entre usuário e grupo (`UserGroup`), não exclui o usuário nem o grupo.
    - Caso o usuário removido seja o próprio solicitante, isso pode ser tratado como **saída voluntária do grupo** (leave group), se desejado.

</details>

<details>
<summary><b>PATCH /groups/{id}/members/{user_id}</b> - Atualiza o papel de um membro no grupo </summary>

- **Descrição:** Atualiza o papel (`role`) de um usuário dentro de um grupo.  
  Apenas o **criador do grupo (owner)** pode executar esta operação.

- **Regras de Permissão:**
    - O **owner** pode:
        - Transferir a posse do grupo para outro usuário (novo `owner`)
        - Tornar um `member` em `admin`
    - O **admin** não pode alterar papéis
    - Um **member** não pode alterar papéis

- **Headers:**
    - `Authorization:` Bearer `<token>`
    - `Content-Type:` application/json

- **Parâmetros de Caminho:**
    - `id` (string, required): o identificador único do grupo  
    - `user_id` (string, required): o identificador do usuário cujo papel será atualizado  

- **Body:**
    - `role` (string, required): novo papel do usuário no grupo  
        - Valores aceitos: `owner`, `admin`

- **Exemplo-Body:**
    ```json
    {
        "role": "admin"
    }
    ```

- **Response:**
    - `group_id` (string): o id do grupo  
    - `user_id` (string): o id do usuário atualizado  
    - `role` (string): o novo papel atribuído ao usuário  
    - `message` (string): mensagem informando o resultado da operação  

- **Códigos:**
    - `200` OK - Papel do usuário atualizado com sucesso  
    - `400` Bad Request - Papel inválido ou campo obrigatório ausente  
    - `401` Unauthorized - Token de autenticação ausente, inválido ou expirado  
    - `403` Forbidden - Usuário autenticado não é o owner do grupo  
    - `404` Not Found - Grupo ou usuário não encontrado, ou usuário não pertence ao grupo  
    - `500` Internal Server Error - Erro interno ao tentar atualizar o papel do membro  

- **Exemplo-Response: [200 OK]**
    ```json
    {
        "group_id": "a3b6f5c2-0f3e-4b9d-9d1b-1c9c9f5b8a21",
        "user_id": "e52dd592-2b42-48ae-a9fd-8c8e9372b982",
        "role": "admin",
        "message": "User role was updated successfully"
    }
    ```

- **Exemplo-Response: [403 Forbidden]**
    ```json
    {
        "message": "Only the group owner can update member roles"
    }
    ```

- **Exemplo-Response: [400 Bad Request]**
    ```json
    {
        "message": "Invalid role. Allowed values are: owner, admin"
    }
    ```

- **OBS.:**
    - Apenas o **owner** pode modificar papéis dentro do grupo.
    - Ao definir `role = "owner"`, o usuário autenticado **deixa de ser owner** e o controle do grupo é transferido.
    - `admin` **não pode promover, rebaixar ou transferir ownership**.
    - `member` **não possui qualquer permissão administrativa**.
    - Não é possível definir o papel como `member` através deste endpoint (rebaixamentos não são permitidos aqui).
    - O usuário alvo deve já ser membro do grupo.

</details>

## Endpoint de Imagens

<details>
<summary><b>GET /images/{filename}</b> - Busca uma imagem no servidor</summary>
</details>

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