import os
import uuid
from werkzeug.utils import secure_filename
from logger import logger

UPLOAD_FOLDER = 'static/pfp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
CDN_BASE_URL = "https://cdn.conchat.app/pfp/"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file_obj, upload_folder):
    if not file_obj:
        return None, None

    try:
        fname, ext = file_obj.filename.rsplit('.', 1)
    except ValueError:
        fname = "unknown"
        ext = "png"

    fname = secure_filename(fname)
    if not fname: 
        fname = "file"

    new_filename = f"{fname}_{uuid.uuid4().hex}.{ext.lower()}"
    full_path = os.path.join(upload_folder, new_filename)

    file_obj.save(full_path)
    return new_filename, full_path

def delete_file(file_path):
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            logger.error(f"An error ocurred while deleting file: {file_path}")
            return False
    return False