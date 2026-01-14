from flask import Flask, Blueprint, request, jsonify
from validate import *
from schema import *
from logger import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_, and_
from filehandling import *
from werkzeug.utils import secure_filename

users_bp = Blueprint("Users Blueprint", __name__, url_prefix='/user')

@users_bp.route("/users", methods=["GET"])
@require_auth()
def search_users(token_payload):
    q = request.args.get('q')
    
    if not q:
        return jsonify({"message": "Query parameter 'q' is required!"}), 400

    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        if page < 1: page = 1
        if limit < 1: limit = 20
        if limit > 50: limit = 50
    except ValueError:
        page = 1
        limit = 20

    offset = (page - 1) * limit

    stmt = select(User).where(User.name.ilike(f"%{q}%")) \
        .offset(offset) \
        .limit(limit)
    
    results = db.session.execute(stmt).scalars().all()

    users_list = []

    for user in results:
        pfp_filename = user.pfp

        users_list.append({
            "username": user.username,
            "uuid": str(user.id),
            "pfp_url": pfp_filename
        })

    return jsonify({
        "users": users_list,
        "message": f"{len(users_list)} users found!"
    }), 200

@users_bp.route("/users", methods=["POST"])
def create_user():
    username = request.form.get("username")
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([username, name, email, password]):
        return jsonify({"message": "Fields required!"}), 400
    
    if len(password) < 8:
         return jsonify({"message": "Password too short"}), 400

    stmt = select(User).where(or_(User.username == username, User.email == email))
    existing_user = db.session.execute(stmt).scalar_one_or_none()

    if existing_user:
        msg = f"Username '{username}' taken" if existing_user.username == username else f"Email '{email}' taken"
        return jsonify({"message": msg}), 409

    pfp_file = request.files.get("pfp")
    pfp_filename = None
    pfp_path = None

    if pfp_file and allowed_file(pfp_file.filename):
        try:
            pfp_filename, pfp_path = save_file(pfp_file, UPLOAD_FOLDER)
        except Exception as e:
            logger.error(f"Error saving profile picture: {e}")
            return jsonify({"message": "Error saving profile picture"}), 500
    
    try:
        hashed_password = hasher.hash(password)
        
        new_user = User(
            username=username,
            name=name, 
            email=email,
            password=hashed_password,
            profile_picture=pfp_filename
        )
        
        db.session.add(new_user)
        db.session.flush()
        
        refresh_token_str, code_status = gen_refresh_token(new_user.id)
        if not refresh_token_str:
             raise Exception("Error generating session")

        access_token = gen_jwt(new_user.id, role="default")
        db.session.commit()
        
        final_pfp_url = f"{CDN_BASE_URL}{pfp_filename}" if pfp_filename else None

        return jsonify({
            "uuid": str(new_user.id),
            "pfp_url": final_pfp_url,
            "created_at": utc_now().isoformat(),
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "message": "User created successfully"
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na transação do banco: {e}")

        delete_file(pfp_path)

        return jsonify({"message": "Internal server error"}), 500
