import mqtt from 'mqtt';

const BROKER_URL = 'ws://localhost:8083/mqtt';

let client = null;

export const connectMQTT = (myUserId, myGroupsList, onMessageReceived) => {
  if (client) return client;

  const fixedClientId = `web_${myUserId}`;

  client = mqtt.connect(BROKER_URL, {
    clientId: fixedClientId,
    clean: false,
    keepalive: 60,
    reconnectPeriod: 1000,
  });

  client.on('connect', () => {
    console.log('Conectado ao EMQX');

    const myTopic = `/dms/${myUserId}`;
    
    client.subscribe(myTopic, { qos : 1 }, (err) => {
      if (!err) {
        console.log(`Escutando canal: ${myTopic}`);
      } else {
        console.error('Erro ao assinar tópico:', err);
      }
    });

    if (myGroupsList && myGroupsList.length > 0) {
      myGroupsList.forEach(group => {
        const groupTopic = `/groups/${group.id}`;
        client.subscribe(groupTopic, { qos: 1 }, (err) => {
          if (!err) console.log(`Ouvindo grupo: ${groupTopic}`);
        });
      });
    }
  });

  client.on('message', (topic, message) => {
    try {
      const payload = JSON.parse(message.toString());
      console.log('Mensagem recebida:', payload);
      onMessageReceived(payload);
    } catch (e) {
      console.error('Erro ao processar mensagem JSON', e);
    }
  });

  client.on('error', (err) => {
    console.error('Erro de conexão MQTT:', err);
    client.end();
  });

  return client;
};

export const sendChatMessage = (targetUserId, myUserId, contentText) => {
  if (!client || !client.connected) {
    console.warn('Cliente não conectado. Tentando reconectar...');
    return;
  }

  const topic = `/dms/${targetUserId}`;
  
  const payload = {
    type: "MESSAGE_NEW",
    from: myUserId,
    timestamp: new Date().toISOString(),
    payload: {
      id: crypto.randomUUID(),
      content: contentText
    }
  };

  client.publish(topic, JSON.stringify(payload));
  console.log(`Enviado para ${topic}`);
};