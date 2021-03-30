from app import app, db
from app.models import Group, User, create_basic_db

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'User': User, 
            'Group': Group, 
            'create_db': create_basic_db}
