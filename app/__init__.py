from flask import Flask
from app import routes
from app.routes import main
from .models import db


def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = "static/uploaded_files"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobbot.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.register_blueprint(main)
    return app

