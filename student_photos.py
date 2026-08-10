"""Store and serve learner profile photos (class teachers upload)."""
import os
import uuid

from flask import current_app, url_for
from werkzeug.utils import secure_filename

ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_BYTES = 2 * 1024 * 1024


def student_photo_dir():
    folder = os.path.join(current_app.instance_path, "student_photos")
    os.makedirs(folder, exist_ok=True)
    return folder


def student_photo_url(learner):
    if not learner or not getattr(learner, "photo_filename", None):
        return None
    return url_for("student_photo", filename=learner.photo_filename)


def delete_student_photo_file(filename):
    if not filename:
        return
    safe = os.path.basename(filename)
    if safe != filename:
        return
    path = os.path.join(student_photo_dir(), safe)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def save_student_photo_upload(file, student_id):
    """
    Validate and save an uploaded image for a learner.
    Returns (filename, error_message). filename is None on failure or empty upload.
    """
    if not file or not getattr(file, "filename", None):
        return None, None

    original = secure_filename(file.filename) or ""
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        return None, "Profile photo must be JPG, PNG, or WebP."

    data = file.read()
    if not data:
        return None, "The profile photo file is empty."
    if len(data) > MAX_PHOTO_BYTES:
        return None, "Profile photo must be 2 MB or smaller."

    stored_name = f"{student_id}_{uuid.uuid4().hex[:12]}{ext}"
    path = os.path.join(student_photo_dir(), stored_name)
    with open(path, "wb") as out:
        out.write(data)
    return stored_name, None


def can_view_student_photo(user, student):
    if not user.is_authenticated or not student:
        return False
    if getattr(user, "role", None) == "superadmin":
        return True
    if not student.school_id or user.school_id != student.school_id:
        return False
    if user.role == "parent":
        return student.parent_id == user.id
    return user.role in ("admin", "teacher", "nurse", "guard")
