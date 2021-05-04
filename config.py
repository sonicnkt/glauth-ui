import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SERVER_NAME = os.environ.get('BASE_URL')
    APPNAME = os.environ.get('APPNAME') or 'Glauth UI'
    ORGANISATION = os.environ.get('ORGANISATION') or 'Glauth UI - Team'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    ADMIN_GROUP = os.environ.get('ADMIN_GROUP') or 'glauth_admin'

    # MAIL Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN') or 'admin@example.com'
    # Gets Errors and is sender of emails send to users

    # Database Stuff
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Glauth Stuff 
    GLAUTH_CFG_PATH = os.environ.get('GLAUTH_CFG_PATH') or \
        os.path.join(basedir, 'db', 'config.cfg')
    
    # FLASK ADMIN STUFF
    FLASK_ADMIN_FLUID_LAYOUT = True
