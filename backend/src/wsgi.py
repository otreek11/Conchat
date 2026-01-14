from .app import *
from src.logger import logger
from flask_cors import CORS

@base_bp.route("/ping", methods = ["GET"])
def ping():
    return jsonify({
        "message": "Servidor está ativo e funcional!",
        "received_at": datetime.now()
    }), 200

logger.info("Initializing Server...")


app = init_app()
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
# Create database tables if they don't exist
with app.app_context():
    from schema import db
    db.create_all()
    logger.info("Database tables created/verified")
    
logger.info("Server started!")
