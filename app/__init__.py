from flask import Flask
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
# https://bootstrap-flask.readthedocs.io
from flask_bootstrap import Bootstrap
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
import hashlib
import os
import click

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
bootstrap = Bootstrap(app)

#from .oauth import blueprint as oauth_blueprint
#app.register_blueprint(oauth_blueprint, url_prefix="/oauth")


if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['MAIL_ADMIN'], subject='{} - Failure'.format(app.config['APPNAME']),
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    # Only log to file if configure in UI?
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/glauth_ui.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('GLauth Management UI')       

# Security - Generate GLAUTH compatible password hashs
def generate_password_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password_hash(hash, password):
    if (hash != hashlib.sha256(password.encode('utf-8')).hexdigest()):
        return False
    return True

from app import routes, models, glauth, adminview, errors

@app.cli.command()
def createdbdata():
    """Creating example db"""
    if models.User.query.count() == 0:
        app.logger.info('No Data in DB, creating example dataset') 
        click.echo('Creating Example DB')
        models.create_basic_db()
    else:
        app.logger.info('Data in DB allready exists.') 
