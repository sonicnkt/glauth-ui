from ast import literal_eval
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    def parse_env(key, default, _type=str):
        if _type == str:
            return os.environ.get(key, default)
        return _type(literal_eval(os.environ.get(key, default)))

    APPNAME      = parse_env('APPNAME', 'Glauth UI')
    ORGANISATION = parse_env('ORGANISATION', 'Glauth UI - Team')
    SECRET_KEY   = parse_env('SECRET_KEY', 'you-will-never-guess')
    ADMIN_GROUP  = parse_env('ADMIN_GROUP', 'glauth_admin')

    BEHAVIORS_IGNORE_CAPABILITIES = parse_env('BEHAVIORS_IGNORE_CAPABILITIES', 'True', bool)

    # MAIL Config
    MAIL_SERVER   = parse_env('MAIL_SERVER', '')
    MAIL_PORT     = parse_env('MAIL_PORT', '25', int)
    MAIL_USE_TLS  = parse_env('MAIL_USE_TLS', 'False', bool)
    MAIL_USERNAME = parse_env('MAIL_USERNAME', '')
    MAIL_PASSWORD = parse_env('MAIL_PASSWORD', '')
    MAIL_ADMIN    = parse_env('MAIL_ADMIN', '')
    MAIL_ERROR_REPORT_FROM = parse_env('MAIL_ERROR_REPORT_FROM', 'no-reply@' + MAIL_SERVER)
    MAIL_ERROR_REPORT_TO   = str.split(parse_env('MAIL_ERROR_REPORT_TO', MAIL_ADMIN))
    # Gets Errors and is sender of emails send to users

    # Database Stuff
    SQLALCHEMY_DATABASE_URI = parse_env('DATABASE_URL', \
        'sqlite:///' + os.path.join(basedir, 'db', 'app.db'))

    # Glauth Stuff 
    GLAUTH_CFG_PATH = parse_env('GLAUTH_CFG_PATH', \
        os.path.join(basedir, 'db', 'config.cfg'))
    
    # FLASK ADMIN STUFF
    FLASK_ADMIN_FLUID_LAYOUT = parse_env('FLASK_ADMIN_FLUID_LAYOUT', 'False', bool)

    FLASK = type('obj', (object,), {
        'MAIL_SERVER': MAIL_SERVER,
        'MAIL_PORT': MAIL_PORT,
        'MAIL_USE_TLS': MAIL_USE_TLS,
        'MAIL_USERNAME': MAIL_USERNAME,
        'MAIL_PASSWORD': MAIL_PASSWORD,
        'SECRET_KEY': SECRET_KEY,
        'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
