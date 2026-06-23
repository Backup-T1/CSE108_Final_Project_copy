import os

from flask import Flask
from flask_login import LoginManager

from config import Config
from app.models import db, User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import auth_bp
    from app.pet import pet_bp
    from app.social import social_bp
    from app.shop import shop_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pet_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(shop_bp)

    from app.utils import item_icon_key
    app.jinja_env.globals["item_icon_key"] = item_icon_key

    with app.app_context():
        db.create_all()

    return app
