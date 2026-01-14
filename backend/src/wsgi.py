from .app import *
from logger import logger

@base_bp.route("/ping", methods = ["GET"])
def ping():
    return jsonify({
        "message": "Servidor está ativo e funcional!",
        "received_at": datetime.now()
    }), 200

logger.info("Initializing Server...")
app = init_app()


logger.info("Server started!")
