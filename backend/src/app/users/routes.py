from flask import Flask, Blueprint, request, jsonify
from ...validate import *
from ...schema import *
from ...logger import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_, and_
from ...filehandling import *
from werkzeug.utils import secure_filename

users_bp = Blueprint("Users Blueprint", __name__, url_prefix='/user')

@users_bp.route("/", methods=["GET"])
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

    # Buscar por username OU name
    stmt = select(User).where(
        or_(
            User.username.ilike(f"%{q}%"),
            User.name.ilike(f"%{q}%")
        )
    ).offset(offset).limit(limit)

    results = db.session.execute(stmt).scalars().all()

    users_list = []

    for user in results:
        if user.id == uuid.UUID(token_payload['sub']): continue # Ignora a si mesmo
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

@users_bp.route("/", methods=["POST"])
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
            pfp=pfp_filename
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


@users_bp.route('/id/<id>', methods=['GET'])
@require_auth()
def get_user_by_id(id, token_payload):
    user = db.session.get(User, uuid.UUID(id))

    if not user:
        return jsonify({
            "message": f"Could not find user '{id}'"
        }), 404

    response_data = {
        "uuid": user.id,
        "username": user.username,
        "name": user.name,
        "created_at": user.registered_at.isoformat(),
        "pfp_url": user.pfp,
        "email": user.email,
        "message": f"User {id} was found"
    }

    requested_fields = request.args.get('fields')
    
    if requested_fields:
        fields_list = [f.strip() for f in requested_fields.split(',')]
        
        filtered_response = {
            k: v for k, v in response_data.items() if k in fields_list
        }

        if filtered_response:
            return jsonify(filtered_response), 200

    return jsonify(response_data), 200

@users_bp.route('/<username>', methods=['GET'])
@require_auth()
def get_user_by_username(username, token_payload):
    user = db.session.query(User).filter_by(username=username).first()

    if not user:
        return jsonify({
            "message": f"Could not find user '{username}'"
        }), 404

    response_data = {
        "uuid": user.id,
        "username": user.username,
        "name": user.name,
        "created_at": user.registered_at.isoformat(),
        "pfp_url": user.pfp,
        "email": user.email,
        "message": f"User {username} was found"
    }

    requested_fields = request.args.get('fields')
    
    if requested_fields:
        fields_list = [f.strip() for f in requested_fields.split(',')]
        
        filtered_response = {
            k: v for k, v in response_data.items() if k in fields_list
        }

        if filtered_response:
            return jsonify(filtered_response), 200

    return jsonify(response_data), 200

@users_bp.route("/<id>", methods=["DELETE"])
@require_auth()
def delete_user(id, token_payload):
    try:
        user = db.session.get(User, id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        requester_id = token_payload.get("sub")
        requester_role = token_payload.get("role")

        if requester_role != "admin" and requester_id != id:
            return jsonify({"message": "Forbidden"}), 403

        db.session.delete(user)
        db.session.commit()

        logger.info(f"User removed: {id}")
        return jsonify({"message": "User removed"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while deleting user {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@users_bp.route("/<id>", methods=["PATCH"])
@require_auth()
def update_user(id, token_payload):
    pfp_path = None
    try:
        user = db.session.get(User, id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        requester_id = token_payload.get("sub")
        requester_role = token_payload.get("role")

        if requester_role != "admin" and requester_id != id:
            return jsonify({"message": "Forbidden"}), 403

        username = request.form.get("username")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        pfp_file = request.files.get("pfp")

        if not any([username, name, email, password, pfp_file]):
            return jsonify({"message": "No fields provided"}), 400

        if password:
            if len(password) < 8:
                return jsonify({"message": "Password too short"}), 400

        filters = []
        if username:
            filters.append(User.username == username)
        if email:
            filters.append(User.email == email)

        if filters:
            stmt = select(User).where(
                and_(
                    User.id != user.id,
                    or_(*filters)
                )
            )

            existing_user = db.session.execute(stmt).scalar_one_or_none()
            if existing_user:
                msg = f"Username '{username}' taken" if username and existing_user.username == username else f"Email '{email}' taken"
                return jsonify({"message": msg}), 409

        if username is not None:
            user.username = username

        if name is not None:
            user.name = name

        if email is not None:
            user.email = email

        if password:
            user.password = hasher.hash(password)

        old_pfp_path = None
        if pfp_file:
            if not allowed_file(pfp_file.filename):
                return jsonify({"message": "Invalid file type"}), 400

            pfp_filename, pfp_path = save_file(pfp_file, UPLOAD_FOLDER)

            if user.pfp:
                old_pfp_path = os.path.join(UPLOAD_FOLDER, user.pfp)

            user.pfp = pfp_filename

        db.session.commit()

        if old_pfp_path:
            delete_file(old_pfp_path)

        final_pfp_url = f"{CDN_BASE_URL}{user.pfp}" if user.pfp else None

        logger.info(f"User updated: {id}")

        return jsonify({
            "uuid": str(user.id),
            "pfp_url": final_pfp_url,
            "message": "User updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()

        if pfp_path:
            delete_file(pfp_path)

        logger.error(f"Error while updating user {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    
@users_bp.route('/<id>/groups', methods=["GET"])
@require_auth()
def get_user_groups(id, token_payload):

    user = db.session.get(User, uuid.UUID(id))
    if not user:
        return jsonify({"message": f"User {id} not found"}), 404
    
    if user.id != uuid.UUID(token_payload['sub']) and token_payload['role'] != 'admin':
        return jsonify({"message": "Forbidden"}), 403
    relations = db.session.query(UserGroup).filter_by(user_id = uuid.UUID(id)).all()

    x = []
    for r in relations:
        x.append({
            "id": str(r.group_id),
            "joined_at": r.entered_at,
            "role": r.role,
        })
    
    return jsonify({
        "message": f"{len(x)} groups found",
        "groups": x,
    }), 200

@users_bp.route('/<id>/friends', methods=["GET"])
@require_auth()
def get_user_friends(id, token_payload):

    user = db.session.get(User, uuid.UUID(id))
    if not user:
        return jsonify({"message": f"User {id} not found"}), 404
    
    if user.id != uuid.UUID(token_payload['sub']) and token_payload['role'] != 'admin':
        return jsonify({"message": "Forbidden"}), 403
    
    uid = uuid.UUID(id)
    stmt = select(Friendship).where(
        and_(
            or_(
                Friendship.addressee_id == uid, 
                Friendship.requester_id == uid
            ),
            Friendship.status == FriendshipStatus.APPROVED
        )
    )

    relations = db.session.execute(stmt).scalars().all()

    x = []
    for r in relations:
        x.append({
            "id": r.requester_id if r.addressee_id == uid else r.addressee_id
        })
    
    return jsonify({
        "message": f"{len(x)} friends found",
        "friends": x,
    }), 200

@users_bp.route('/<target_id>/friends/request', methods=['POST'])
@require_auth()
def send_friend_request(target_id, token_payload):
    requester_id = uuid.UUID(token_payload['sub'])
    
    try:
        addressee_id = uuid.UUID(target_id)
    except ValueError:
        return jsonify({"message": "Invalid Target UUID"}), 400

    if requester_id == addressee_id:
        return jsonify({"message": "You cannot friend yourself"}), 400

    target_user = db.session.get(User, addressee_id)
    if not target_user:
        return jsonify({"message": "User not found"}), 404

    existing_friendship = Friendship.get_between(requester_id, addressee_id)

    if existing_friendship:
        if existing_friendship.status == FriendshipStatus.APPROVED:
            return jsonify({"message": "Already friends"}), 409
        
        if existing_friendship.status == FriendshipStatus.PENDING:
            if existing_friendship.requester_id == requester_id:
                return jsonify({"message": "Request already sent"}), 409
            else:
                return jsonify({"message": "This user already sent you a request. Accept it instead."}), 409
        
        if existing_friendship.status == FriendshipStatus.REJECTED:
            if existing_friendship.requester_id != requester_id:
                db.session.delete(existing_friendship)
                db.session.flush()
            else:

                existing_friendship.status = FriendshipStatus.PENDING
                existing_friendship.created_at = utc_now()
                db.session.commit()
                return jsonify({"message": "Friend request resent"}), 200

    new_friendship = Friendship(
        requester_id=requester_id,
        addressee_id=addressee_id,
        status=FriendshipStatus.PENDING
    )

    db.session.add(new_friendship)
    db.session.commit()

    # Publicar evento MQTT para notificar o destinatário
    try:
        from src.app.emqx.mqtt_publisher import MQTTPublisher

        requester = db.session.get(User, requester_id)
        MQTTPublisher.publish_event(
            topic=f"/users/{str(addressee_id)}",
            event_type="FRIENDREQUEST_RECEIVED",
            from_user_id=requester_id,
            payload={
                "requester_id": str(requester_id),
                "requester_username": requester.username,
                "requester_name": requester.name,
                "requester_pfp_url": requester.pfp
            }
        )
    except Exception as e:
        logger.error(f"Error publishing MQTT event: {e}")

    return jsonify({"message": "Friend request sent successfully"}), 201

@users_bp.route('/<requester_id>/friends/request', methods=['PATCH'])
@require_auth()
def respond_friend_request(requester_id, token_payload):
    my_id = uuid.UUID(token_payload['sub'])
    
    try:
        req_id = uuid.UUID(requester_id)
    except ValueError:
        return jsonify({"message": "Invalid Requester UUID"}), 400

    data = request.get_json()
    action = data.get('action')

    if action not in ['accept', 'reject']:
        return jsonify({"message": "Action must be 'accept' or 'reject'"}), 400

    friendship = db.session.query(Friendship).filter_by(
        requester_id=req_id,
        addressee_id=my_id
    ).first()

    if not friendship:
        return jsonify({"message": "Friend request not found"}), 404

    if friendship.status != FriendshipStatus.PENDING:
        return jsonify({"message": f"This request is already {friendship.status.value}"}), 409

    if action == 'accept':
        friendship.status = FriendshipStatus.APPROVED
        msg = "Friend request accepted"
    else:
        friendship.status = FriendshipStatus.REJECTED
        msg = "Friend request rejected"

    db.session.commit()

    # Publicar evento MQTT para notificar o remetente original
    try:
        from src.app.emqx.mqtt_publisher import MQTTPublisher

        my_user = db.session.get(User, my_id)
        MQTTPublisher.publish_event(
            topic=f"/users/{str(req_id)}",
            event_type="FRIENDSTATUS_UPDATE",
            from_user_id=my_id,
            payload={
                "action": action,
                "user_id": str(my_id),
                "username": my_user.username,
                "name": my_user.name,
                "pfp_url": my_user.pfp
            }
        )
    except Exception as e:
        logger.error(f"Error publishing MQTT event: {e}")

    return jsonify({
        "message": msg,
        "current_status": friendship.status.value
    }), 200

@users_bp.route('/<id>/friends/requests/pending', methods=['GET'])
@require_auth()
def get_pending_requests(id, token_payload):
    """Lista convites de amizade pendentes recebidos pelo usuário"""
    user = db.session.get(User, uuid.UUID(id))
    if not user:
        return jsonify({"message": f"User {id} not found"}), 404

    if user.id != uuid.UUID(token_payload['sub']) and token_payload['role'] != 'admin':
        return jsonify({"message": "Forbidden"}), 403

    uid = uuid.UUID(id)
    stmt = select(Friendship).where(
        and_(
            Friendship.addressee_id == uid,
            Friendship.status == FriendshipStatus.PENDING
        )
    )

    requests = db.session.execute(stmt).scalars().all()

    result = []
    for req in requests:
        requester = db.session.get(User, req.requester_id)
        if requester:
            result.append({
                "requester_id": str(requester.id),
                "requester_username": requester.username,
                "requester_name": requester.name,
                "requester_pfp_url": requester.pfp,
                "created_at": req.created_at.isoformat()
            })

    return jsonify({
        "message": f"{len(result)} pending requests found",
        "requests": result
    }), 200