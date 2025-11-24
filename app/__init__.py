from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

application = Flask(__name__)
application.config.from_object(Config)

db = SQLAlchemy(application)
login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes

with application.app_context():
    db.create_all()