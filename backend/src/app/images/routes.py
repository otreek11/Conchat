import os
from flask import Blueprint, send_from_directory, abort
from werkzeug.utils import secure_filename
from src.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # abominacao
BASE_STATIC_PATH = os.path.join(BASE_DIR, "static")

images_bp = Blueprint("Images Blueprint", __name__, url_prefix="/images")

@images_bp.route("/<filename>", methods=["GET"])
def get_file(filename):

    safe_name = secure_filename(filename)
    folder = os.path.join(BASE_STATIC_PATH, "uploads")

    file_path = os.path.join(folder, safe_name)
    logger.info(f"Attempt to load file: {file_path}")
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder, safe_name)