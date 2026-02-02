import requests
import time

EMQX_API = "http://localhost:18083/api/v5"
AUTH = ("admin", "public")

def configure():
    authn_body = {
        "mechanism": "password_based",
        "backend": "built_in_database",
        "user_id_type": "username"
    }

    requests.post(f"{EMQX_API}/authentication", json=authn_body, auth=AUTH)

    authz_body = {
        "type": "built_in_database",
        "enable": True
    }
    requests.post(f"{EMQX_API}/authorization/sources", json=authz_body, auth=AUTH)

if __name__ == "__main__":
    configure()