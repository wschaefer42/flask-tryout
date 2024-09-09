import logging
import traceback
from logging.config import dictConfig
from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy

from app import types
from config import configurations, Config

bootstrap = Bootstrap5()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
moment = Moment()
mail = Mail()
pagedown = PageDown()
config: Config = Config()

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
        "loggers": {
            "trace": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False,
            }
        },
    }
)

trace = logging.getLogger("trace")


def create_app(config_name):
    global config
    config = configurations[config_name]
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['SECRET_KEY'] = 'any secret string'

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    pagedown.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .hello import hello as hello_blueprint
    app.register_blueprint(hello_blueprint, url_prefix='/hello')
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    from .post import post as post_blueprint
    app.register_blueprint(post_blueprint, url_prefix='/post')
    from .profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint, url_prefix='/profile')
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.context_processor
    def add_imports():
        return dict(types=types)

    @app.errorhandler(Exception)
    def internal_error(e):
        print(traceback.format_exc())
        return render_template('errors/500.html', error=e), 500

    return app
