from flask import Flask, Blueprint, request, jsonify
from ...validate import *
from ...schema import *
from ...logger import logger
from sqlalchemy.exc import IntegrityError


auth_bp = Blueprint("Authorization Blueprint", __name__, url_prefix='/auth')

@auth_bp.route("/login", methods = ["POST"])
def login():
    req = request.get_json()

    username = req.get('username')
    senha = req.get("password")

    if not username or not senha:
        return jsonify({"message": "'username' and 'password' are required"}), 400
    
    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({"message": "Wrong credentials"}), 401
    
    try:
        hasher.verify(user.password, senha)
    except VerifyMismatchError:
        return jsonify({"message": "Wrong credentials"}), 401
        
    refresh, code = gen_refresh_token(user.id)
    if refresh is None:
        return jsonify({"message": "We could not process login, please try again later"}), code

    role = 'default'
    if user.admin_profile:
        role = 'admin'
    
    access_tok = gen_jwt(user.id, role)

    return jsonify({
        "message": "Login successful!",
        "refresh_token": refresh,
        "access_token": access_tok,
    }), 200

@auth_bp.route('/me', methods=['GET'])
@require_auth()
def me_info(token_payload):
    id = token_payload['sub']
    role = token_payload['role']

    return jsonify({
        'uuid': id,
        'role': role, 
    }), 200

@auth_bp.route("/refresh", methods = ["POST"])
def refresh():
    req = request.get_json()
    ref_tok = req.get("refresh_token")

    if not ref_tok:
        return jsonify({"message": "'refresh_token' is required"}), 400
    
    return validate_refresh_token(ref_tok)
