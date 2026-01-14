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

# Create database tables if they don't exist
with app.app_context():
    from schema import db
    db.create_all()
    logger.info("Database tables created/verified")

logger.info("Server started!")
