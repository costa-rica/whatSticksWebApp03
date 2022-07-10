from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from whatSticksWebApp.config import Config
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import logging
import sys
import os

from whatSticksWebApp.utils import logs_dir
from logging.handlers import RotatingFileHandler

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_init = logging.getLogger('app_package')
logger_init.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(logs_dir,'__init__.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

logger_init.addHandler(file_handler)


#set werkzeug handler
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('werkzeug').addHandler(file_handler)
#End set up logger

logger_init.info(f'Starting App')


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager= LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()

#application factory
def create_app(config_class=Config):
    app = Flask(__name__)

    # logger = logging.getLogger(__name__)
    # stderr_handler = logging.StreamHandler(sys.stderr)
    # logger.addHandler(stderr_handler)
    # file_handler = logging.FileHandler('whatSticksWebApp_log.txt')
    # file_handler.setLevel(logging.DEBUG)
    # logger.addHandler(file_handler)
    # app.logger.addHandler(file_handler)

    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    from whatSticksWebApp.main.routes import main
    from whatSticksWebApp.posts.routes import posts
    from whatSticksWebApp.users.routes import users
    # from whatSticksWebApp.errors.handlers import errors
    app.register_blueprint(main)
    app.register_blueprint(posts)
    app.register_blueprint(users)
    # app.register_blueprint(errors)


    return app
