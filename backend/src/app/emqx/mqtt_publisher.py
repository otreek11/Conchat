import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone
from src.logger import logger

MQTT_BROKER = "emqx"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "public"

class MQTTPublisher:
    @staticmethod
    def publish_event(topic, event_type, from_user_id, payload):
        """
        Publishes an MQTT event to a topic.

        Args:
            topic: MQTT topic (e.g., "/users/uuid-123")
            event_type: Event type (e.g., "FRIENDREQUEST_RECEIVED")
            from_user_id: UUID of the user triggering the event
            payload: Dictionary with event-specific data
        """
        try:
            client = mqtt.Client()
            client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
            client.connect(MQTT_BROKER, MQTT_PORT, 60)

            event = {
                "type": event_type,
                "from": str(from_user_id),
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            message = json.dumps(event)
            result = client.publish(topic, message, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published {event_type} to {topic}")
            else:
                logger.error(f"Failed to publish {event_type} to {topic}: {result.rc}")

            client.disconnect()
            return True

        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False
