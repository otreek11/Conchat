from app import *
from src.logger import logger

@base_bp.route("/")
def index():
    return {"message": "Hello World!"}, 200

@base_bp.route("/ping", methods = ["GET"])
def ping():
    return jsonify({
        "message": "Servidor está ativo e funcional!",
        "received_at": datetime.now(timezone.utc)
    }), 200

if __name__ == "__main__":
    logger.info("Initializing Server...")

    app = init_app()
    app.register_blueprint(base_bp)
    

    logger.info("Initializing database...")
    with app.app_context():
        db.create_all()
    
    logger.info("Database initialized!")
    
    logger.info("Starting up server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
    logger.info("Server stopped.")
