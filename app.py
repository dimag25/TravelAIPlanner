import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Load the appropriate configuration
    if os.environ.get('FLASK_ENV') == 'production':
        from config.production import CONFIG
        app.config.update(CONFIG)
    else:
        app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'

    return app

app = create_app()

from models import User
from populate_templates import populate_templates

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and populate templates within app context
with app.app_context():
    try:
        import models
        db.create_all()
        populate_templates()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
