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
<summary><b>MÉTODO ENDPOINT - DESC</b> </summary>

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

# Arquitetura Pub/Sub

A arquitetura Pub/Sub foi implementada para fins de comunicação entre clientes no app. Clientes publicam mensagens para o Broker utilizando o protocolo MQTT, e então o Broker repassa as mensagens para outros clientes inscritos naquele grupo.

O Broker utilizado no projeto foi o **EMQX**, sua escolha foi com base em uma análise intensa comparando os brokers Apache Kafka (Que apesar de não ser MQTT, ainda sim analisamos), Mosquitto e EMQX.

- **Apache Kafka:** O Kafka se demonstra extremamente forte em suas funcionalidades, e é de fato muito consistente e escalável, contudo seu overhead é muito elevado para uma aplicação mobile, além de que modificar permissões (quais clientes podem ler/enviar mensagens em quais grupos) pode se demonstrar uma tarefa de complexidade demasiadamente elevada.

- **Mosquitto:** O Broker Mosquitto é um broker muito simples que permite que facilmente seja implementado o protocolo MQTT para comunicação, contudo seu uso real para a aplicação seria complexo, já que ele apenas possui nativamente controle de permissão estático, sendo necessário ou reiniciar o broker a cada modificação de permissão (inviável) ou utilizar plugins que permitem que essas permissões sejam modificadas dinamicamente (complexo)

- **EMQX:** O Broker EMQX é ainda um broker MQTT relativamente simples de ser implementado, podendo ser utilizado ainda via Docker (facilita o deploy), e permite que implementemos nativamente a checagem de permissões definindo WebHooks para nosso backend cuidar da checagem, além de facilitar a mudança dessas permissões durante a execução do broker.

Após a análise, escolhemos utilizar o broker EMQX, por utilizar ainda o protocolo MQTT (o que é mais eficiente para uma aplicação mobile) e possuir a maioria das funcionalidades que são necessárias para a construção do aplicativo.

Tal arquitetura ainda permite (caso haja necessidade para uma maior robustez/escalabilidade) integrarmos o EMQX com o Kafka, onde os usuários enviam mensagens para o broker EMQX (eficiente) e o broker envia para o Kafka (escalável), mantendo o melhor de ambos os mundos sem aumentar a complexidade para os usuários.