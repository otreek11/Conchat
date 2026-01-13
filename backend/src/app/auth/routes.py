from flask import Blueprint, jsonify

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/ping', methods=['GET'])
def ping_auth():
	return jsonify({'message': 'auth OK'}), 200

