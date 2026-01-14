from flask import Flask, Blueprint, request, jsonify
from src.validate import *
from src.schema import *
from src.logger import logger
from src.filehandling import *
from sqlalchemy.exc import IntegrityError

groups_bp = Blueprint("Groups Blueprint", __name__, url_prefix="/groups")

@groups_bp.route("", methods=["POST"])
@require_auth()
def create_group(token_payload):
    try:
        user_id = token_payload.get("sub")

        name = request.form.get("name")
        icon_file = request.files.get("icon")

        size = request.form.get("size", 128)

        if not name or not name.strip():
            return jsonify({"message": "'name' field must be provided!"}), 400

        group = Group(name=name.strip(), max_users=size)

        if icon_file:
            if not allowed_file(icon_file.filename):
                return jsonify({"message": "Invalid file type"}), 400

            icon_filename, icon_path = save_file(icon_file, UPLOAD_FOLDER)
            group.icon = icon_filename

        db.session.add(group)
        db.session.flush()

        user_group = UserGroup(
            user_id=user_id,
            group_id=group.id,
            role="owner"
        )

        db.session.add(user_group)
        db.session.commit()

        icon_url = f"{CDN_BASE_URL}{group.icon}" if group.icon else None

        logger.info(f"Group created: {group.id} by user {user_id}")

        return jsonify({
            "uuid": str(group.id),
            "name": group.name,
            "icon_url": icon_url,
            "registered_at": group.registered_at.isoformat(),
            "message": "Group was created successfully"
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Conflict while creating group"}), 409

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while creating group: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500


@groups_bp.route("/<id>", methods=["DELETE"])
@require_auth()
def delete_group(id, token_payload):
    try:
        group = db.session.get(Group, id)
        if not group:
            return jsonify({"message": "Group not found"}), 404

        requester_id = token_payload.get("sub")
        requester_role = token_payload.get("role")

        is_creator = False

        creator_relation = db.session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=requester_id,
            role="owner"
        ).first()

        if creator_relation:
            is_creator = True

        if requester_role != "admin" and not is_creator:
            return jsonify({"message": "Forbidden"}), 403

        old_icon_path = None
        if group.icon:
            old_icon_path = os.path.join(UPLOAD_FOLDER, group.icon)

        db.session.delete(group)
        db.session.commit()

        if old_icon_path:
            delete_file(old_icon_path)

        logger.info(f"Group deleted: {id}")

        return jsonify({
            "message": "Group was deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while deleting group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    
@groups_bp.route("/<id>", methods=["PATCH"])
@require_auth()
def update_group(id, token_payload):
    try:
        group = db.session.get(Group, uuid.UUID(id))
        if not group:
            return jsonify({"message": "Group not found"}), 404

        requester_id = token_payload.get("sub")
        requester_role = token_payload.get("role")

        creator_relation = db.session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=requester_id,
            role="owner"
        ).first()

        is_creator = creator_relation is not None

        if requester_role != "admin" and not is_creator:
            return jsonify({"message": "Forbidden"}), 403

        name = request.form.get("name")
        icon_file = request.files.get("icon")

        if not name and not icon_file:
            return jsonify({"message": "No valid fields provided"}), 400

        if name is not None:
            if not name.strip():
                return jsonify({"message": "'name' field cannot be empty"}), 400
            group.name = name.strip()

        old_icon_path = None

        if icon_file:
            if not allowed_file(icon_file.filename):
                return jsonify({"message": "Invalid file type"}), 400

            if group.icon:
                old_icon_path = os.path.join(UPLOAD_FOLDER, group.icon)

            icon_filename, icon_path = save_file(icon_file, UPLOAD_FOLDER)
            group.icon = icon_filename

        db.session.commit()

        if old_icon_path:
            delete_file(old_icon_path)

        icon_url = f"{CDN_BASE_URL}{group.icon}" if group.icon else None

        logger.info(f"Group updated: {id} by user {requester_id}")

        return jsonify({
            "uuid": str(group.id),
            "name": group.name,
            "icon_url": icon_url,
            "message": "Group was updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while updating group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    

@groups_bp.route("/<id>/members", methods=["POST"])
@require_auth()
def add_group_member(id: str, token_payload):
    try:
        requester_id: str = token_payload.get("sub")

        data = request.get_json()
        if not data:
            return jsonify({"message": "Request body must be JSON"}), 400

        user_id: str = data.get("user_id")
        role = data.get("role", "member")

        if not user_id:
            return jsonify({"message": "'user_id' field must be provided!"}), 400

        if role not in ["member", "admin"]:
            return jsonify({"message": "Invalid role"}), 400

        group = db.session.get(Group, uuid.UUID(id))
        if not group:
            return jsonify({"message": "Group not found"}), 404

        user = db.session.get(User, uuid.UUID(user_id))
        if not user:
            return jsonify({"message": "User not found"}), 404

        requester_relation = db.session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=uuid.UUID(requester_id)
        ).first()

        if not requester_relation or requester_relation.role not in ["owner", "admin"]:
            return jsonify({"message": "Forbidden"}), 403

        existing_relation = db.session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=uuid.UUID(user_id)
        ).first()

        if existing_relation:
            return jsonify({"message": "User is already a member of this group"}), 409

        with db.session.begin():
            members_count = db.session.query(UserGroup).filter_by(
                group_id=group.id
            ).with_for_update().count()

            if members_count >= group.max_users:
                return jsonify({
                    "message": f"This group has reached the maximum number of members ({group.max_users})"
                }), 400

            user_group = UserGroup(
                user_id=uuid.UUID(user_id),
                group_id=group.id,
                role=role
            )

            db.session.add(user_group)

        logger.info(f"User {user_id} added to group {group.id} by {requester_id}")

        return jsonify({
            "group_id": str(group.id),
            "user_id": str(user_id),
            "role": role,
            "message": "User was added to group successfully"
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while adding user {user_id} to group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500

@groups_bp.route("/<id>/members/<user_id>", methods=["DELETE"])
@require_auth()
def remove_member(id, user_id, token_payload):
    try:
        requester_id = token_payload.get("sub")

        group = db.session.get(Group, uuid.UUID(id))
        if not group:
            return jsonify({"message": "Group not found"}), 404

        target_relation = db.session.query(UserGroup).filter_by(
            group_id=uuid.UUID(id),
            user_id=uuid.UUID(user_id)
        ).first()

        if not target_relation:
            return jsonify({"message": "User is not a member of this group"}), 404

        requester_relation = db.session.query(UserGroup).filter_by(
            group_id=uuid.UUID(id),
            user_id=uuid.UUID(requester_id),
        ).first()

        if not requester_relation:
            return jsonify({"message": "You are not a member of this group"}), 403

        requester_role = requester_relation.role
        target_role = target_relation.role

        is_self = requester_id == user_id

        if is_self and requester_role == "owner":
            return jsonify({"message": "Owner cannot leave the group, a transfer is necessary"}), 403
        
        if is_self:
            db.session.delete(target_relation)
            db.session.commit()

            logger.info(f"User {user_id} left group {id}")

            return jsonify({
                "group_id": id,
                "user_id": user_id,
                "message": "User left the group successfully"
            }), 200

        # owner expulsa outra pessoa
        if requester_role == "owner":
            db.session.delete(target_relation)
            db.session.commit()

            logger.info(f"User {user_id} removed from group {id} by owner {requester_id}")

            return jsonify({
                "group_id": id,
                "user_id": user_id,
                "message": "User was removed from group successfully"
            }), 200

        # admin expulsa membro
        if requester_role == "admin":
            if target_role != "member":
                return jsonify({"message": "Admin can only remove members"}), 403

            db.session.delete(target_relation)
            db.session.commit()

            logger.info(f"User {user_id} removed from group {id} by admin {requester_id}")

            return jsonify({
                "group_id": id,
                "user_id": user_id,
                "message": "User was removed from group successfully"
            }), 200

        # membro tentando expulsar outra pessoa
        return jsonify({"message": "Forbidden"}), 403

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while removing user {user_id} from group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    
@groups_bp.route("/<id>/members/<user_id>", methods=["PATCH"])
@require_auth()
def update_member_role(id, user_id, token_payload):
    try:
        requester_id = token_payload.get("sub")

        group = db.session.get(Group, uuid.UUID(id))
        if not group:
            return jsonify({"message": "Group not found"}), 404

        requester_relation = db.session.query(UserGroup).filter_by(
            group_id=uuid.UUID(id),
            user_id=uuid.UUID(requester_id)
        ).first()

        if not requester_relation:
            return jsonify({"message": "You are not a member of this group"}), 403

        if requester_relation.role != "owner":
            return jsonify({"message": "Only the group owner can update member roles"}), 403

        target_relation = db.session.query(UserGroup).filter_by(
            group_id=uuid.UUID(id),
            user_id=uuid.UUID(user_id)
        ).first()

        if not target_relation:
            return jsonify({"message": "User is not a member of this group"}), 404

        data = request.get_json()
        if not data or "role" not in data:
            return jsonify({"message": "'role' field must be provided"}), 400

        new_role = data.get("role")

        if new_role not in ["owner", "admin"]:
            return jsonify({"message": "Invalid role. Allowed values are: owner, admin"}), 400

        if new_role == "owner":
            if str(user_id) == str(requester_id):
                return jsonify({"message": "You are already the owner"}), 400

            target_relation.role = "owner"

            requester_relation.role = "admin"

        elif new_role == "admin":
            if target_relation.role == "owner":
                return jsonify({"message": "Cannot change role of the owner"}), 400

            target_relation.role = "admin"

        db.session.commit()

        logger.info(
            f"User {user_id} role updated to '{new_role}' in group {id} by owner {requester_id}"
        )

        return jsonify({
            "group_id": id,
            "user_id": user_id,
            "role": new_role,
            "message": "User role was updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error while updating role for user {user_id} in group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500
    
@groups_bp.route("/<id>/members", methods=["GET"])
@require_auth()
def list_members(id, token_payload):
    try:
        requester_id = token_payload.get("sub")

        group = db.session.get(Group, uuid.UUID(id))
        if not group:
            return jsonify({"message": "Group not found"}), 404

        requester_relation = db.session.query(UserGroup).filter_by(
            group_id=uuid.UUID(id),
            user_id=uuid.UUID(requester_id)
        ).first()

        if not requester_relation:
            return jsonify({"message": "You are not a member of this group"}), 403

        role_filter = request.args.get("role")
        query = db.session.query(UserGroup).filter_by(group_id=uuid.UUID(id))

        if role_filter:
            if role_filter not in ["owner", "admin", "member"]:
                return jsonify({
                    "message": "Invalid role filter. Allowed values are: owner, admin, member"
                }), 400
            query = query.filter_by(role=role_filter)

        relations = query.all()

        members = []
        for rel in relations:
            members.append({
                "user_id": str(rel.user_id),
                "role": rel.role,
                "joined_at": rel.entered_at,
            })

        return jsonify({
            "group_id": id,
            "members": members
        }), 200

    except ValueError:
        return jsonify({"message": "Invalid group id"}), 400

    except Exception as e:
        logger.error(f"Error while listing members of group {id}: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500