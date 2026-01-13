from flask import Blueprint, jsonify

admins_bp = Blueprint('admins_bp', __name__, url_prefix='/admins')


@admins_bp.route('/ping', methods=['GET'])
def ping_admins():
	return jsonify({'message': 'admins OK'}), 200
