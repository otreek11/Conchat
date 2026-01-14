import os, uuid

from flask import Flask, Blueprint, request, jsonify
from dotenv import load_dotenv
from src.schema import *
from src.validate import *

base_bp = Blueprint("Base API Blueprint", __name__, url_prefix="/api/v1")

def init_app():
    load_dotenv()
    
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    
    from .auth import auth_bp
    from .users import users_bp
    from .admins import admins_bp

    base_bp.register_blueprint(auth_bp)
    base_bp.register_blueprint(users_bp)
    base_bp.register_blueprint(admins_bp)
    
    app.register_blueprint(base_bp)

    return app