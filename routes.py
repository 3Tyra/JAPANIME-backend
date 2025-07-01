from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from extensions import db
import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

routes_bp = Blueprint("routes", __name__, url_prefix="/api")

@routes_bp.route("/upload-photo", methods=["POST"])
@jwt_required()
def upload_photo():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if 'photo' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    user.profile_photo = f"https://japanime-backend.onrender.com/{unique_filename}"
    db.session.commit()

    return jsonify({
        "message": "Photo uploaded successfully",
        "filename": unique_filename,
        "profile_photo": user.profile_photo
    }), 200

@routes_bp.route("/remove-photo", methods=["POST"])
@jwt_required()
def remove_photo():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.profile_photo:
        return jsonify({"error": "No profile photo to remove"}), 400

    filename = user.profile_photo.split("/")[-1]
    file_path = os.path.join(current_app.root_path, "uploads", filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    user.profile_photo = None
    db.session.commit()

    return jsonify({"message": "Profile photo removed"}), 200

@routes_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "email": user.email,
        "age": user.age,
        "created_at": user.created_at.isoformat(),
        "profile_photo": user.profile_photo,
    })

@routes_bp.route("/update-profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "age" in data:
        user.age = data["age"]
    if "password" in data and data["password"]:
        user.set_password(data["password"])  

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "username": user.username,
        "email": user.email,
        "age": user.age,
        "profile_photo": user.profile_photo
    })

@routes_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("identifier")
    password = data.get("password")
    if not identifier or not password:
        return jsonify({"error": "Missing username/email or password"}), 400

    user = User.query.filter(
        or_(User.email == identifier, User.username == identifier)
    ).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200
