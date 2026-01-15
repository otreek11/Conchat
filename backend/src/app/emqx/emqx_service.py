import requests
import json
from src.logger import logger

EMQX_HOST = "http://emqx:18083/api/v5"
AUTH = ("admin", "public")

class EmqxService:
    @staticmethod
    def create_user(username, password):
        """Cria o usuário no EMQX para ele poder logar"""
        try:
            url = f"{EMQX_HOST}/authentication/password_based:built_in_database/users"
            payload = {
                "user_id": username,
                "password": password 
            }
            res = requests.post(url, json=payload, auth=AUTH)
            if res.status_code not in [200, 201, 409]: # 409 = ja existe
                logger.error(f"Erro criando user MQTT: {res.text}")
            
            # Já cria as regras iniciais (DMs)
            EmqxService.set_initial_rules(username)
            
        except Exception as e:
            logger.error(f"FALHA EMQX: {e}")

    @staticmethod
    def set_initial_rules(username):
        """Define que o usuário pode ler/escrever nas suas DMs"""
        rules = [
            # Pode assinar/publicar nas próprias DMs e Perfil
            {"action": "all", "permission": "allow", "topic": f"/dms/{username}"},
            {"action": "all", "permission": "allow", "topic": f"/users/{username}"},
            # Pode MANDAR mensagem pra qualquer DM (pra conversa funcionar)
            {"action": "publish", "permission": "allow", "topic": "/dms/+"},
             # Pode MANDAR mensagem pra qualquer User (convite de amizade)
            {"action": "publish", "permission": "allow", "topic": "/users/+"}
        ]
        EmqxService._update_rules(username, rules)

    @staticmethod
    def add_group_access(username, group_id):
        """Pega as regras atuais e adiciona o grupo"""
        current_rules = EmqxService._get_rules(username)
        
        # Cria regra do grupo
        new_rule = {"action": "all", "permission": "allow", "topic": f"/groups/{group_id}"}
        
        # Evita duplicados
        if new_rule not in current_rules:
            current_rules.append(new_rule)
            EmqxService._update_rules(username, current_rules)

    @staticmethod
    def _get_rules(username):
        try:
            url = f"{EMQX_HOST}/authorization/sources/built_in_database/rules/users/{username}"
            res = requests.get(url, auth=AUTH)
            if res.status_code == 200:
                return res.json().get('rules', [])
            return []
        except:
            return []

    @staticmethod
    def _update_rules(username, rules):
        try:
            url = f"{EMQX_HOST}/authorization/sources/built_in_database/rules/users/{username}"
            payload = {"rules": rules}
            requests.put(url, json=payload, auth=AUTH)
        except Exception as e:
            logger.error(f"Erro atualizando regras: {e}")