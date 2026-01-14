import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

def decode_jwt(token):
    """
    Decodifica e valida um token JWT.
    Retorna o payload se válido, None caso contrário.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def validate_jwt(token):
    """
    Valida se um token JWT é válido e não expirado.
    Retorna (True, payload) se válido, (False, None) caso contrário.
    """
    payload = decode_jwt(token)
    if payload is None:
        return False, None
    return True, payload
