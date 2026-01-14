import os
from flask import Flask
from dotenv import load_dotenv
from shared.schema import db
from webhooks import webhooks_bp
from logger import logger

def init_app():
    load_dotenv()

    app = Flask(__name__)

    # Configuração do banco de dados (mesmo do backend)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar DB
    db.init_app(app)

    # Registrar blueprints
    app.register_blueprint(webhooks_bp)

    return app

if __name__ == "__main__":
    logger.info("Initializing Webhooks Server...")
    app = init_app()

    logger.info("Starting up webhooks server on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=True)
