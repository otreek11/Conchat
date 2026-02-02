"""
Lógica de autorização ACL para tópicos MQTT.
Implementa as regras de negócio definidas na arquitetura.
"""
from shared.schema import db, UserGroup, Friendship, FriendshipStatus
from logger import logger
import re
from uuid import UUID

def check_group_access(user_uuid, group_uuid):
    """
    Verifica se o usuário é membro do grupo.

    Args:
        user_uuid: UUID do usuário (string)
        group_uuid: UUID do grupo (string)

    Returns:
        bool: True se o usuário é membro, False caso contrário
    """
    try:
        user_id = UUID(user_uuid)
        group_id = UUID(group_uuid)

        membership = db.session.query(UserGroup).filter_by(
            user_id=user_id,
            group_id=group_id
        ).first()

        return membership is not None
    except (ValueError, Exception) as e:
        logger.error(f"Error checking group access: {e}")
        return False

def check_friendship(user_uuid, friend_uuid):
    """
    Verifica se existe amizade aprovada entre os usuários.

    Args:
        user_uuid: UUID do usuário (string)
        friend_uuid: UUID do amigo (string)

    Returns:
        bool: True se são amigos aprovados, False caso contrário
    """
    try:
        user_id = UUID(user_uuid)
        friend_id = UUID(friend_uuid)

        friendship = Friendship.get_between(user_id, friend_id)

        if friendship and friendship.status == FriendshipStatus.APPROVED:
            return True
        return False
    except (ValueError, Exception) as e:
        logger.error(f"Error checking friendship: {e}")
        return False

def authorize_topic_access(user_uuid, topic, action):
    """
    Autoriza acesso a um tópico baseado nas regras de negócio.

    Args:
        user_uuid: UUID do usuário fazendo a requisição (extraído do JWT)
        topic: Tópico MQTT (ex: /groups/{uuid})
        action: 'publish' ou 'subscribe'

    Returns:
        tuple: (bool, str) - (permitido, mensagem)
    """

    # Regex patterns para cada tipo de tópico
    group_pattern = r'^/groups/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'
    dm_pattern = r'^/dms/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'
    user_pattern = r'^/users/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'

    # REGRA 1: Tópico de grupo /groups/{group_uuid}
    group_match = re.match(group_pattern, topic, re.IGNORECASE)
    if group_match:
        group_uuid = group_match.group(1)

        # Tanto PUBLISH quanto SUBSCRIBE requerem ser membro do grupo
        if check_group_access(user_uuid, group_uuid):
            logger.info(f"User {user_uuid} authorized to {action} on group {group_uuid}")
            return True, f"User is member of group {group_uuid}"
        else:
            logger.warning(f"User {user_uuid} denied {action} on group {group_uuid} - not a member")
            return False, f"User is not a member of group {group_uuid}"

    # REGRA 2: Tópico de DM /dms/{user_uuid}
    dm_match = re.match(dm_pattern, topic, re.IGNORECASE)
    if dm_match:
        target_user_uuid = dm_match.group(1)

        if action == 'subscribe':
            # SUBSCRIBE: apenas o próprio usuário
            if user_uuid.lower() == target_user_uuid.lower():
                logger.info(f"User {user_uuid} authorized to subscribe to own DMs")
                return True, "User can subscribe to own DM topic"
            else:
                logger.warning(f"User {user_uuid} denied subscribe to DM {target_user_uuid}")
                return False, "Can only subscribe to own DM topic"

        elif action == 'publish':
            # PUBLISH: apenas amigos aprovados
            if check_friendship(user_uuid, target_user_uuid):
                logger.info(f"User {user_uuid} authorized to publish DM to friend {target_user_uuid}")
                return True, f"User is friend with {target_user_uuid}"
            else:
                logger.warning(f"User {user_uuid} denied publish to DM {target_user_uuid} - not friends")
                return False, f"User is not friend with {target_user_uuid}"

    # REGRA 3: Tópico de usuário /users/{user_uuid}
    user_match = re.match(user_pattern, topic, re.IGNORECASE)
    if user_match:
        target_user_uuid = user_match.group(1)

        if action == 'subscribe':
            # SUBSCRIBE: apenas o próprio usuário
            if user_uuid.lower() == target_user_uuid.lower():
                logger.info(f"User {user_uuid} authorized to subscribe to own user topic")
                return True, "User can subscribe to own user topic"
            else:
                logger.warning(f"User {user_uuid} denied subscribe to user topic {target_user_uuid}")
                return False, "Can only subscribe to own user topic"

        elif action == 'publish':
            # PUBLISH: apenas o sistema (negar todos)
            logger.warning(f"User {user_uuid} denied publish to user topic - system only")
            return False, "Only system can publish to user topics"

    # Tópico não reconhecido
    logger.warning(f"Unknown topic pattern: {topic}")
    return False, f"Topic {topic} does not match any known pattern"
