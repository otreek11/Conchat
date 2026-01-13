import jwt, os, secrets, uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from .schema import *
from flask import jsonify, request
from functools import wraps

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_EXP = timedelta(hours=1) # Token de acesso dura 1 hora
REFRESH_EXP = timedelta(days=30) # 30 dias de inatividade

hasher = PasswordHasher()


# Decorador
def require_auth(role = None):
    def dec(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization")
            if auth is None:
                return jsonify({"message": "Token was not provided!"}), 400

            parts = auth.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"message": "Malformed authorization header"}), 400

            token = parts[1]
            payload = decodeJWT(token)
            if payload is None: # Token invalido/expirado
                return jsonify({"message": "Token is invalid/expired"}), 401
            
            user_role = payload["role"]
            if role is not None and user_role != role:
                return jsonify({"message": "The specified user is not allowed to perform such action"}), 403
            
            return func(*args, tokenPayload=payload, **kwargs)
        return wrapper
    return dec
            
def fakeRequireAuth(role=None):
    print("Using fake authenticator")
    def dec(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            payload = {
                "user_code": 0,
                "user_id": "this user is not real",
                "exp": datetime.now(tz=timezone.utc) + REFRESH_EXP, # dura muito tempo
                "role": "admin"
            }

            return func(*args, tokenPayload=payload, **kwargs)
        return wrapper
    return dec



# JWT ------------------------------------------------------------------------------------------------------------------
def gen_jwt(user_id, role):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + ACCESS_EXP
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    
# REFRESH -----------------------------------------------------------------------------------------------------------------

def gen_refresh_token(user_id):
    token_secret = secrets.token_urlsafe(64)
    token_hash = hasher.hash(token_secret)
    expires_at = datetime.now(timezone.utc) + REFRESH_EXP

    token = RefreshToken (
        token_hash = token_hash,
        expires_at = expires_at,
        user_id = user_id
    )

    try:
        db.session.add(token)
        db.session.commit()
    except:
        return None, 500

    return f"{token.token_id}.{token_secret}", 200

def validate_refresh_token(token):
    try:
        tok_id, tok_sec = token.split(".")
    except ValueError:
        return jsonify({"message": "Malformed token"}), 400

    db_token = db.session.get(RefreshToken, tok_id)
    if not db_token:
        return jsonify({"message": "Token not found"}), 404
    
    # Expirado
    if db_token.expires_at < datetime.now(timezone.utc):
        return jsonify({"message": "Expired token"}), 401
    
    if not db_token.is_valid:
        return jsonify({"message": "Invalid token"}), 401
    
    # Verifica Hash do token
    try:
        hasher.verify(db_token.token_hash, tok_sec)
    except VerifyMismatchError: 
        # Inválido (perigoso, tem alguém tentando utilizar um token de sessão não existente para a conta)
        # Invalidamos todos os tokens daquela conta, forçando a fazer login novamente
        db.session.query(RefreshToken).filter_by(user_id = db_token.user_id).update({"is_valid": False})

        try:
            db.session.commit()
        except:
            db.session.rollback()
            return jsonify({"message": "The specified token has an invalid hash, but we were not able to invalidate it"}), 500
        return jsonify({"message": "O Token apresentado tem hash inválido"}), 401
    
    # Válido
    newSecretTok = secrets.token_urlsafe(64)
    newHash = hasher.hash(newSecretTok)
    newExpires = datetime.now(timezone.utc) + REFRESH_EXP

    db_token.TokenHash = newHash
    db_token.ExpiraEm = newExpires


    try:
        db.session.commit()
    except:
        return jsonify({"message": "Não foi possível salvar o token validado"}), 500
    
    role = "client"
    
    admin = db.session.query(Admin).filter_by(CodAdmin = db_token.CodUsuario).first()
    if admin: role = "admin"
    else:
        seller = db.session.query(Vendedor).filter_by(CodVendedor = db_token.CodUsuario).first()
        if seller: role = "seller"
    
    user = db.session.query(Usuario).filter_by(CodUsuario = db_token.CodUsuario).first()


    return jsonify({
        "message": "Token é válido e foi atualizado com sucesso",
        "refresh_token": f"{codTok}.{newSecretTok}",
        "access_token": genJWT(user.UsuarioUUID, user.CodUsuario, role)
    }), 200

def cleanupExpiredTokens():
    now = datetime.now(timezone.utc)
    tokens = db.session.query(RefreshToken).filter(RefreshToken.ExpiraEm < now).all()

    for token in tokens:
        db.session.delete(token)

    try:
        db.session.commit()
    except:
        return False
    
    return True
