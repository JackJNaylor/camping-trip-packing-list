from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import LoginManager


def create_app():
    app = Flask(__name__)

    app.config['MONGODB_SETTINGS'] = {
        'db': 'Packer',
        'host': 'mongodb+srv://jacknaylor:mongoPass@cluster0.xohuk.mongodb.net/Packer?retryWrites=true&w=majority'
    }

    db = MongoEngine(app)
    app.config['SECRET_KEY'] = 'klasjdlkhjlkgjoqi9ejlinalksdjhflkjaee'
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(pk=user_id).first()

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
