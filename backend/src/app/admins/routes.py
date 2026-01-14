from flask import Flask, Blueprint, request, jsonify
from validate import *
from schema import *
from logger import logger
from sqlalchemy.exc import IntegrityError

admins_bp = Blueprint("Administrators Blueprint", __name__, url_prefix="/admins")

@admins_bp.route("/", methods=["POST"])
@require_auth(role="admin")
def create_admin(tokenPayload):
    req = request.get_json(silent=True) or {}

    id = req.get("public_id")
    if not id:
        return jsonify({"message": "'public_id' required"}), 400
    
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    admin = Admin(id=user.id)
    
    try:
        db.session.add(admin)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "User is admin already"}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Error while registering user as admin"}), 500
    
    logger.info(f"User was registered as admin: {id}")
    return jsonify({"message": "Admin was registered!"}), 200

@admins_bp.route("/<id>", methods=["DELETE"])
@require_auth(role="admin")
def delete_admin(id, tokenPayload):
    admin = db.session.get(Admin, id)
    if not admin:
        return jsonify({"message": "User is not admin"}), 404

    try:
        db.session.delete(admin)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.error(f"There was an error while unregistering user as admin: {id}")
        return jsonify({"message": "There was an error while unregistering user as admin"}), 500
    
    logger.info(f"User is no longer admin: {id}")
    return jsonify({"message": "User is no longer admin"}), 200


