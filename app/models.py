from app import app, db, generate_password_hash, check_password_hash, login
from flask_login import UserMixin
from time import time
import jwt


othergroups_users = db.Table(
    'othergroups_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.unixid')),
    db.Column('group_id', db.Integer(), db.ForeignKey('group.unixid'))
)

included_groups = db.Table(
    'included_groups',
    db.Column('include_id', db.Integer(), db.ForeignKey('group.unixid')),
    db.Column('included_in_id', db.Integer(), db.ForeignKey('group.unixid'))
)


# Glauth Configuration
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    debug = db.Column(db.Boolean, default=True, nullable=False)
    ldap_enabled = db.Column(db.Boolean, default=True)
    ldap_listen = db.Column(db.String(40))
    ldaps_enabled = db.Column(db.Boolean, default=False)
    ldaps_listen = db.Column(db.String(40))
    ldaps_cert = db.Column(db.String(40))
    ldaps_key = db.Column(db.String(40))
    basedn = db.Column(db.String(40))
    nameformat = db.Column(db.String(4)) # Default "cn"
    groupformat = db.Column(db.String(4)) # Default "ou"
    sshkeyattr = db.Column(db.String(20)) # Default "ipaSshPubKey"
    def __repr__(self):
        return 'GLAUTH Config Object'

# Groups
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True, unique=True, nullable=False)
    unixid = db.Column(db.Integer, unique=True, nullable=False)
    primary = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.String(255))
    p_users = db.relationship('User', backref='pgroup', lazy='dynamic')
    included_in = db.relationship('Group', secondary=included_groups,
                            primaryjoin=(included_groups.c.include_id == unixid),
                            secondaryjoin=(included_groups.c.included_in_id == unixid),
                            backref=db.backref('includes', lazy='dynamic'), lazy='dynamic')
    def __repr__(self):
        return '{}'.format(self.name)
            


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), index=True, unique=True, nullable=False)
    mail = db.Column(db.String(50), index=True, unique=True)
    givenname = db.Column(db.String(40)) #, index=True)
    surname = db.Column(db.String(40)) #, index=True)
    unixid = db.Column(db.Integer, unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    # add activation date?
    primarygroup = db.Column(db.Integer, db.ForeignKey('group.unixid'), nullable=False)
    othergroups = db.relationship('Group', secondary=othergroups_users,
                            backref=db.backref('o_users', lazy='dynamic'))

    @property
    def is_admin(self):
        # checks if the name of any group matches the configured ADMIN_GROUP name
        if [group for group in self.othergroups if group.name == app.config['ADMIN_GROUP']]:
            return True
        return False
    
    def __repr__(self):
        if self.givenname and self.username:
            return '{} {}'.format(self.givenname, self.surname)
        return '{}'.format(self.username)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    def get_new_account_token(self, expires_in=86400):
        return jwt.encode(
            {'username': self.username, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    def in_groups(self,*allowed_groups):
        """Check if the user is in a group
        """
        primarygroup=Group.query.filter_by(unixid=self.primarygroup).first()
        if primarygroup.name in allowed_groups:
            return True
        for group in self.othergroups:
            if group.name in allowed_groups:
                return True
        return False

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    @staticmethod
    def verify_new_account_token(token):
        try:
            username = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['username']
        except:
            return
        return User.query.filter_by(username=username).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


def create_basic_db():
    settings = Settings(debug=True, ldap_enabled=True, ldap_listen='0.0.0.0:389', basedn='dc=glauth-example,dc=com')
    
    db.session.add(settings)

    og1 = Group(name='glauth_admin', unixid=5551, description='Glauth UI admin group')
    og2 = Group(name='vpn', unixid=5552)

    db.session.add(og1)
    db.session.add(og2)

    pg1 = Group(name='people', unixid=5501, primary=True, description='primary user group', includes=[ og2 ])
    pg2 = Group(name='svcaccts', unixid=5502, primary=True, description='service accounts')
   
    db.session.add(pg1)
    db.session.add(pg2)

    u1 = User(username='j_doe', givenname='Jane', surname='Doe', unixid=5001, password_hash='6478579e37aff45f013e14eeb30b3cc56c72ccdc310123bcdf53e0333e3f416a', mail='jane.doe@glauth-example.com', pgroup=pg1, othergroups=[og1])
    # PW: dogood
    u2 = User(username='search', unixid=5002, password_hash='125844054e30fabcd4182ae69c9d7b38b58d63c067be10ab5ab883d658383316', pgroup=pg2)
    # PW: searchpw
    db.session.add(u1)
    db.session.add(u2)
    
    db.session.commit()