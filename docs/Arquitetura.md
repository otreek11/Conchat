# Arquitetura

Esse documento busca esclarecer a arquitetura utilizada para o aplicativo Conchat, explicando e documentando tanto como funciona quanto justificando seu uso específico.

## Visão Geral

A arquitetura da aplicação se trata de uma hibridização entre as arquiteturas RESTful e Publish-Subscribe. 

- **RESTful:** Utilizada para autenticação e autorização em ações internas à aplicação, além de prover outras funcionalidades como a descoberta de novos usuários

- **Publish-Subscribe:** Utilizada para envio e recebimento de mensagens e eventos no geral (como pedidos de amizade ou convite para chat), a filosofia utilizada para a arquitetura foi a de "Shared Data Space", já que um usuário enviando uma mensagem não precisa necessariamente saber o local do receptor (Referencialmente desacoplado) e uma mensagem deve ter a garantia de ser eventualmente recebida, mesmo que seu receptor não esteja conectado no momento(Temporalmente desacoplado)

# Arquitetura RESTful
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
    - `message` (string): uma mensagem detalhando o resultado da requisição
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

# Arquitetura Pub/Sub

A arquitetura Pub/Sub foi implementada para fins de comunicação entre clientes no app. Clientes publicam mensagens para o Broker utilizando o protocolo MQTT, e então o Broker repassa as mensagens para outros clientes inscritos naquele grupo.

O Broker utilizado no projeto foi o **EMQX**, sua escolha foi com base em uma análise intensa comparando os brokers Apache Kafka (Que apesar de não ser MQTT, ainda sim analisamos), Mosquitto e EMQX.

- **Apache Kafka:** O Kafka se demonstra extremamente forte em suas funcionalidades, e é de fato muito consistente e escalável, contudo seu overhead é muito elevado para uma aplicação mobile, além de que modificar permissões (quais clientes podem ler/enviar mensagens em quais grupos) pode se demonstrar uma tarefa de complexidade demasiadamente elevada.

- **Mosquitto:** O Broker Mosquitto é um broker muito simples que permite que facilmente seja implementado o protocolo MQTT para comunicação, contudo seu uso real para a aplicação seria complexo, já que ele apenas possui nativamente controle de permissão estático, sendo necessário ou reiniciar o broker a cada modificação de permissão (inviável) ou utilizar plugins que permitem que essas permissões sejam modificadas dinamicamente (complexo)

- **EMQX:** O Broker EMQX é ainda um broker MQTT relativamente simples de ser implementado, podendo ser utilizado ainda via Docker (facilita o deploy), e permite que implementemos nativamente a checagem de permissões definindo WebHooks para nosso backend cuidar da checagem, além de facilitar a mudança dessas permissões durante a execução do broker.

Após a análise, escolhemos utilizar o broker EMQX, por utilizar ainda o protocolo MQTT (o que é mais eficiente para uma aplicação mobile) e possuir a maioria das funcionalidades que são necessárias para a construção do aplicativo.

Tal arquitetura ainda permite (caso haja necessidade para uma maior robustez/escalabilidade) integrarmos o EMQX com o Kafka, onde os usuários enviam mensagens para o broker EMQX (eficiente) e o broker envia para o Kafka (escalável), mantendo o melhor de ambos os mundos sem aumentar a complexidade para os usuários.