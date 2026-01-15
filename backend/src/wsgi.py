from .app import *
from src.logger import logger
from flask_cors import CORS
from src.validate import *

@base_bp.route("/ping", methods = ["GET"])
def ping():
    return jsonify({
        "message": "Servidor está ativo e funcional!",
        "received_at": datetime.now()
    }), 200

@base_bp.route('/mqtt/auth', methods=['POST'])
def mqtt_webhook_auth():
    data = request.get_json()
    
    mqtt_username = data.get('username')
    mqtt_password = data.get('password')

    if not mqtt_username or not mqtt_password:
        return jsonify({"result": "deny"}), 400

    try:
        
        payload = decode_jwt()
        if str(payload['sub']) != mqtt_username:
            # print(f"Tentativa de spoofing: Token é de {payload['sub']} mas user é {mqtt_username}")
            return jsonify({"result": "deny"}), 403

        # print(f"Usuário {mqtt_username} autenticado no MQTT via JWT")
        return jsonify({"result": "allow"}), 200

    except jwt.ExpiredSignatureError:
        # print("Token expirado")
        return jsonify({"result": "deny"}), 403
    except jwt.InvalidTokenError:
        # print("Token inválido")
        return jsonify({"result": "deny"}), 403
    except Exception as e:
        # print(f"Erro no webhook: {e}")
        return jsonify({"result": "deny"}), 500

logger.info("Initializing Server...")

app = init_app()
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

logger.info("Server started!")
