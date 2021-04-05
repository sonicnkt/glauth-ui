import os
from flask import Flask, Blueprint

blueprint = Blueprint('oauth', __name__,
                template_folder='templates')

#Make sure these get imported after the blueprint is already initialized.
#Otherwise there are circular import issues.
from .models import db
from .oauth2 import config_oauth
from .routes import bp
