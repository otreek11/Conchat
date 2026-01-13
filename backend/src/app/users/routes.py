from flask import Blueprint, request, jsonify

users_bp = Blueprint('users_bp', __name__, url_prefix='/users')


@users_bp.route('/ping', methods=['GET'])
def ping_users():
	return jsonify({'message': 'users OK'}), 200
