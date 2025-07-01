import os
from flask import Flask, send_from_directory
from extensions import db, jwt, migrate, limiter, cors
from auth import auth_bp
from routes import routes_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure uploads directory exists
    uploads_path = os.path.join(os.getcwd(), "uploads")
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)
        print(f"Created uploads folder at {uploads_path}")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)

    # Route to serve uploaded files (profile photos)
    @app.route("/uploads/<path:filename>")
    def serve_uploaded_file(filename):
        return send_from_directory("uploads", filename)

    return app
