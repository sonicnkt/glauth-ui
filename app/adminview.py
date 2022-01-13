from app import app, db #, admin
from app.models import User, Group, Settings
from app.forms import EditGlauthForm
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user, logout_user
from flask import flash, redirect, url_for, request, abort
from app.email import send_password_reset_email, send_account_invite

# Custom Forms and Fields for FlaskAdmin
from wtforms import PasswordField, BooleanField, Form
from wtforms.validators import Length, Email, ValidationError
import re

# Create Random password
from random import choices
from string import ascii_uppercase, ascii_lowercase, digits

# Glauth
from app.glauth import create_glauth_config

# Create View classes with custom authentication
class MyBaseView(BaseView):
    def is_accessible(self):
        if current_user.is_authenticated and current_user.is_admin:
            return True
            # integrate true admin check 
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)
        return redirect(url_for('login', next=request.path))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated and current_user.is_admin:
            return True
            # integrate true admin check 
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)
        return redirect(url_for('login', next=request.path))


class MyModelView(ModelView):
    
    def is_accessible(self):
        if current_user.is_authenticated and current_user.is_admin:
            return True
            # integrate true admin check 
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)
        return redirect(url_for('login', next=request.path))


    # can_edit = True
    edit_modal = True
    create_modal = False    
    can_export = True
    can_view_details = False
    details_modal = False

class UserView(MyModelView):
    # Custom Validator Functions
    def valid_chars(self, field):
        result = re.compile(r'[^a-z0-9_-]').search(field.data)
        if result:
            raise ValidationError('"{}" is not allowed'.format(result.group(0)))
    
    # Maybe a configureable list of forbidden usernames stored in config?
    def no_root_allowed(self, field):
        if field.data == 'root':
            raise ValidationError('"root" is not allowed')

    can_view_details = True
    details_modal = True
    # Set custom column öabels
    column_labels = dict(username='Username',
                         givenname='Givenname',
                         surname='Surname',
                         pgroup='Primary Group', 
                         othergroups='Other Groups', 
                         is_active='Active',
                         mail='Email Address',
                         unixid='UnixID')
    # Configure columns in list view (order and which to show)
    column_list = ('username', 'givenname', 'surname', 'mail', 'unixid', 'is_active', 'pgroup') #, 'othergroups')
    # Configure columns that are editable in list view
    column_editable_list = ['username', 'mail', 'givenname', 'surname', 'is_active']
    # Configure columns that a searchable
    column_searchable_list = column_editable_list
    # Configure columns to exclude in list view
    column_exclude_list = ['password_hash']
    # Details View List
    column_details_list = ('username', 'givenname', 'surname', 'mail', 'unixid', 'is_active', 'pgroup')

    # Configure colums to exclude in edit/create view
    form_excluded_columns = column_exclude_list
    
    # Add custom Fields
    form_extra_fields = {
        'password': PasswordField('Password', 
                                  render_kw={"autocomplete": "new-password"},
                                  description='TEMP'),
        'send_pw_reset_link': BooleanField('Send Password Reset Link'),
        # Make this a button in the list view?
        'send_invite_link': BooleanField('Send Invite Link')
    }

    # Add Validators to form
    # Custom Validators https://stackoverflow.com/questions/22947083/flask-admin-modelview-custom-validation
    # TODO: simplyfied username (only ascii + numbers and -_)
    form_args = dict(
        mail = dict(validators=[Email(message='No valid email address')]),
        username = dict(validators=[valid_chars, no_root_allowed, Length(min=4, message='Username must have a minimum of 4 characters')])
    )

    # Configure which form fields to show
    form_columns = ('send_pw_reset_link', 'send_invite_link', 'username', 'password', 'givenname', 'surname', 'mail', 'unixid', 'is_active', 'pgroup', 'othergroups')

    # Configure which columns are shown in detail view
    column_details_exclude_list = ['password_hash']
    
    # Configure which filters can be applied
    column_filters = column_editable_list
    
    # Customize EDIT/Create Form , obj = model object, needs to return a valid form Object in the End
    # Use this to customize which fields are available on new or edited users
    def create_form(self, obj=None):
        form = super(UserView, self).create_form(obj)
        # Delete a form attribute
        delattr(form, 'send_pw_reset_link')
        # Modify query result for query form
        # Primarygroup.query.filter(Primarygroup.name.like('%test%')).all()
        form.pgroup.query = Group.query.filter_by(primary=True).all()
        form.othergroups.query = Group.query.filter_by(primary=False).all()

        # Add Password field description
        form.password.description = 'Leave empty if you want to autogenerate a password.'

        default_unixid=5001
        highest_user=User.query.order_by(User.unixid.desc()).limit(1).all()
        if highest_user:
            default_unixid=highest_user[0].unixid+1
        form.unixid.data=default_unixid
        return form
    
    def edit_form(self, obj):
        form = super(UserView, self).create_form(obj)
        #form.send_pw_reset_link.label = TEST
        # Delete a form attribute
        delattr(form, 'send_invite_link')
        # Change form attribute?
        #setattr(form, 'TEST', BooleanField('DummyTest') )
        
        # Add Password field description
        form.password.description = 'Leave empty to keep the current password.'

        # Modify query result for query form
        # Primarygroup.query.filter(Primarygroup.name.like('%test%')).all()
        form.pgroup.query = Group.query.filter_by(primary=True).all()
        form.othergroups.query = Group.query.filter_by(primary=False).all()
        return form

    # What to do if data is changed
    def on_model_change(self, form, model, is_created):
        # is_created = True if new model/user
        # model = User object
        # form = Form object (form.<columnname>.data)

        # If new users was created without password
        if is_created:
            if form.send_invite_link.data and ((not form.mail.data) or form.mail.data == '' ):
                raise ValidationError('A valid Email Address is required for sending invite links.')
            if not form.password.data or form.password.data == '':
                # Generate random password
                password = ''.join(choices(ascii_uppercase + ascii_lowercase + digits, k=8))
                model.set_password(password)
                # If Send Activation Link Option Enabled
                if form.send_invite_link.data and (form.mail.data != ('' or None)):
                    model.is_active = False
                    # errors with threaded emails wont get caught...
                    send_account_invite(model)
                    flash('Email with activation link was send to  {}'.format(model.mail))
                else:
                    flash('Autogenerated password for new user {}: {}'.format(model.username, password))
            else:
                model.set_password(form.password.data)

        else:
            # If Password Field attribute exists
            if hasattr(form, 'password'):
                # If Attribute Value is not ''
                if form.password.data != '':
                    # Create password hash from password
                    model.set_password(form.password.data)
            # If Reset PW Optione is enabled
            if hasattr(form, 'send_pw_reset_link'):
                if form.send_pw_reset_link.data and ((not form.mail.data) or form.mail.data == '' ):
                    raise ValidationError('A valid Email Address is required for sending password reset links.')
                if form.send_pw_reset_link.data:
                    # Disable Account
                    model.is_active = False
                    send_password_reset_email(model)
                    flash('Reset Password Link was send to  {}'.format(model.mail))
        
        # Write new glauth config File
        try:
            create_glauth_config()
        except Exception:
            pass
    
    # What to do if entry is deleted
    def after_model_delete(self, model):
        # Write new glauth config File
        try:
            create_glauth_config()
        except Exception:
            pass

class GroupView(MyModelView):
    # Custom Validator Functions
    def valid_chars(self, field):
        result = re.compile(r'[^a-z0-9_-]').search(field.data)
        if result:
            raise ValidationError('"{}" is not allowed'.format(result.group(0)))
    
    # Set custom column öabels
    column_labels = dict(p_users='Users', 
                         o_users='Users',
                         name='Name',
                         description='Description',
                         primary='Primary Group', 
                         unixid='UnixID',
                         included_in='Included in Group(s)',
                         includes='Includes Group(s)')
    # Configure columns in list view (order and which to show)
    column_list = ('name', 'unixid', 'primary', 'description')
    # Configure columns that are editable in list view
    column_editable_list = []
    # Configure columns that a searchable
    column_searchable_list = ['name', 'unixid', 'primary', 'description']
    # Configure columns to exclude in list view
    #column_exclude_list = ['password_hash']
    
    column_details_list = ('name', 'unixid', 'primary', 'description', 'includes')

    # Sort by primary then name
    column_default_sort = [('primary', True), ('name', False)]

    # Configure colums to exclude in edit/create view
    #form_excluded_columns = column_exclude_list

    # Add Validators to form
    # Custom Validators https://stackoverflow.com/questions/22947083/flask-admin-modelview-custom-validation
    # TODO: simplyfied name (only ascii + numbers and -_)
    form_args = dict(
        name = dict(validators=[valid_chars, Length(min=3, message='Group names have to be atleast 3* characters long')]),
    )

    # Configure which form fields to show
    form_columns = ('name', 'unixid', 'primary', 'description', 'includes', 'included_in', 'p_users', 'o_users')

    # Configure which columns are shown in detail view
    column_details_exclude_list = ['password_hash']
    
    # Configure which filters can be applied
    column_filters = column_editable_list

    # Customize View depending on primary True/False?

    # Customize EDIT/Create Form , obj = model object, needs to return a valid form Object in the End
    # Use this to customize which fields are available on new or edited users
    def create_form(self, obj=None):
        form = super(GroupView, self).create_form(obj)
        # Delete a form attribute
        delattr(form, 'includes')
        delattr(form, 'included_in')
        delattr(form, 'p_users')
        delattr(form, 'o_users')
        default_unixid=5500
        highest_group=Group.query.order_by(Group.unixid.desc()).limit(1).all()
        if highest_group:
            default_unixid=highest_group[0].unixid+1
        form.unixid.data=default_unixid
        return form
    
    def edit_form(self, obj):
        form = super(GroupView, self).create_form(obj)
        if obj.primary == True:
            # If primary group delete othergroups users 
            delattr(form, 'o_users')
            delattr(form, 'included_in')
        else:
            delattr(form, 'p_users')
        # Dont allow group type change
        delattr(form, 'primary')
        # Only allow non primary groups as includes
        form.includes.query = Group.query.filter_by(primary=False).all()

        return form

    # What to do if data is created or changed
    def on_model_change(self, form, model, is_created):
        # is_created = True if new model/user
        # model = User object
        # form = Form object (form.<columnname>.data)

        # Write new glauth config File
        try:
            create_glauth_config()
        except Exception:
            pass
    
    # What to do if entry is deleted
    def after_model_delete(self, model):
        # Write new glauth config File
        try:
            create_glauth_config()
        except Exception:
            pass

## Customize Base and AdminIndex View with custom is accessible rules (current_user.is_admin)?

class LeaveAdmin(MyBaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('index'))

class GlauthConfig(MyBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = EditGlauthForm()
        settings = Settings.query.get(1)
        
        nameformat = "cn"
        groupformat = "ou"
        if settings.nameformat and (settings.nameformat != ""):
            nameformat = settings.nameformat
        if settings.groupformat and (settings.groupformat != ""):
            groupformat = settings.groupformat            
        dnformat = '{}=<username>,{}=<primarygroup>,{}'.format(nameformat, groupformat, settings.basedn)

        if form.validate_on_submit():
            # Store edited data in db and write to config
            settings.debug = form.debug.data
            settings.ldap_enabled = form.ldap_enabled.data
            settings.ldap_listen = form.ldap_listen.data
            settings.ldaps_enabled = form.ldaps_enabled.data
            settings.ldaps_listen = form.ldaps_listen.data
            settings.ldaps_cert = form.ldaps_cert.data
            settings.ldaps_key = form.ldaps_key.data
            settings.basedn = form.basedn.data
            settings.nameformat = form.nameformat.data
            settings.groupformat = form.groupformat.data
            settings.sshkeyattr = form.sshkeyattr.data

            db.session.commit()
            try:
                create_glauth_config()
                flash('Glauth settings have been changed, please restart glauth server.')
            except Exception as exc:
                flash('Glauth settings NOT updated, an error occured: ' + str(exc))
            
        if request.method == 'GET':
            # Populate form with stored config
            form.debug.data = settings.debug
            form.ldap_enabled.data = settings.ldap_enabled
            form.ldap_listen.data = settings.ldap_listen
            form.ldaps_enabled.data = settings.ldaps_enabled
            form.ldaps_listen.data = settings.ldaps_listen
            form.ldaps_cert.data = settings.ldaps_cert
            form.ldaps_key.data = settings.ldaps_key
            form.basedn.data = settings.basedn
            form.nameformat.data =  settings.nameformat
            form.groupformat.data = settings.groupformat
            form.sshkeyattr.data =  settings.sshkeyattr
        return self.render('admin/glauth.html', form=form, dnformat=dnformat)

class AdminHomeView(MyAdminIndexView):
    @expose('/')
    def index(self):
        counts = {'users': '{}'.format(User.query.count()),
                'pgroups': '{}'.format(Group.query.filter_by(primary=True).count()),
                'ogroups': '{}'.format(Group.query.filter_by(primary=False).count())
                }

        return self.render('admin/myindex.html', counts=counts)



# Initialize Flask ADMIN
admin = Admin(app, name='{} - Admin'.format(app.config['APPNAME']),template_mode='bootstrap4', index_view=AdminHomeView(menu_icon_type='fa', menu_icon_value='fa-home'))

# Add model views
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name="Users"))
admin.add_view(GroupView(Group, db.session, menu_icon_type='fa', menu_icon_value='fa-server', name="Groups"))
admin.add_view(GlauthConfig(name="Settings", menu_icon_type='fa', menu_icon_value='fa-cog'))
admin.add_view(LeaveAdmin(name="Exit", menu_icon_type='fa', menu_icon_value='fa-arrow-circle-right'))


# TODO
#   - prepopulate unixid with function that checks this?
