from flask import Blueprint, request, jsonify
from shared.validate import validate_jwt
from .acl_logic import authorize_topic_access
from logger import logger

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks/v1")

@webhooks_bp.route("/connect", methods=["POST"])
def connect():
    """
    Webhook para autenticação de conexão MQTT.

    Body esperado:
    {
        "clientid": "string",
        "username": "string",
        "password": "JWT_TOKEN"
    }

    Response:
    {
        "result": "allow" | "deny",
        "message": "..."
    }
    """
    try:
        data = request.get_json()

        if not data:
            logger.warning("Connect webhook called with no JSON body")
            return jsonify({"result": "deny", "message": "No JSON body provided"}), 400

        clientid = data.get("clientid")
        username = data.get("username")
        jwt_token = data.get("password")  # JWT vem no campo password

        if not all([clientid, username, jwt_token]):
            logger.warning(f"Connect webhook missing fields - clientid: {clientid}, username: {username}")
            return jsonify({"result": "deny", "message": "Missing required fields"}), 400

        # Validar JWT
        is_valid, payload = validate_jwt(jwt_token)

        if not is_valid:
            logger.warning(f"Invalid JWT for client {clientid}")
            return jsonify({"result": "deny", "message": "JWT expired or invalid"}), 401

        user_uuid = payload.get("sub")
        logger.info(f"Client {clientid} (user {user_uuid}) authenticated successfully")

        return jsonify({
            "result": "allow",
            "message": "Connection authorized"
        }), 200

    except Exception as e:
        logger.error(f"Error in connect webhook: {e}")
        return jsonify({"result": "deny", "message": "Internal server error"}), 500

@webhooks_bp.route("/acl_auth", methods=["POST"])
def acl_auth():
    """
    Webhook para autorização ACL (publish/subscribe em tópicos).

    Body esperado:
    {
        "clientid": "string",
        "username": "string",
        "password": "JWT_TOKEN",
        "topic": "/groups/{uuid}",
        "action": "publish" | "subscribe"
    }

    Response:
    {
        "result": "allow" | "deny",
        "message": "..."
    }
    """
    try:
        data = request.get_json()

        if not data:
            logger.warning("ACL webhook called with no JSON body")
            return jsonify({"result": "deny", "message": "No JSON body provided"}), 400

        clientid = data.get("clientid")
        username = data.get("username")
        jwt_token = data.get("password")
        topic = data.get("topic")
        action = data.get("action")  # 'publish' ou 'subscribe'

        if not all([clientid, username, jwt_token, topic, action]):
            logger.warning(f"ACL webhook missing fields")
            return jsonify({"result": "deny", "message": "Missing required fields"}), 400

        # Validar JWT
        is_valid, payload = validate_jwt(jwt_token)

        if not is_valid:
            logger.warning(f"Invalid JWT for ACL check on topic {topic}")
            return jsonify({"result": "deny", "message": "JWT expired or invalid"}), 401

        user_uuid = payload.get("sub")

        # Verificar autorização no tópico
        allowed, message = authorize_topic_access(user_uuid, topic, action)

        if allowed:
            return jsonify({
                "result": "allow",
                "message": message
            }), 200
        else:
            return jsonify({
                "result": "deny",
                "message": message
            }), 403

    except Exception as e:
        logger.error(f"Error in ACL webhook: {e}")
        return jsonify({"result": "deny", "message": "Internal server error"}), 500

@webhooks_bp.route("/ping", methods=["GET"])
def ping():
    """Endpoint de health check"""
    return jsonify({"message": "Webhooks server is active"}), 200
