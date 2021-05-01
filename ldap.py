from app import app, db
from app.models import Group, User, Settings, create_basic_db

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'User': User, 
            'Group': Group,
            'Settings': Settings, 
            'create_db': create_basic_db}
