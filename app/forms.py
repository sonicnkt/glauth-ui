from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User
from app import check_password_hash

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class TestMailForm(FlaskForm):
    mail = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Mail')   

class EditProfileForm(FlaskForm):
    givenname = StringField('Givenname', validators=[DataRequired(), Length(min=2, max=40)])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=40)])
    mail = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Save')
    cancel = SubmitField(label='Cancel', render_kw={'formnovalidate': True})
    
    def __init__(self, original_mail, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_mail = original_mail

    def validate_mail(self, mail):
        if mail.data != self.original_mail:
            user = User.query.filter_by(mail=self.mail.data).first()
            if user is not None:
                raise ValidationError('Please use a different email.')

class ChangePasswordForm(FlaskForm):
    oldpassword = PasswordField('Current Password', validators=[DataRequired()], render_kw={'autocomplete': 'off'})
    newpassword1 = PasswordField('New Password', validators=[DataRequired()], render_kw={'autocomplete': 'new-password'})
    newpassword2 = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=6, max=20), EqualTo('newpassword1')],
                                 render_kw={'autocomplete': 'new-password'})
    submit = SubmitField('Change Password')
    cancel = SubmitField(label='Cancel', render_kw={'formnovalidate': True})

    def __init__(self, old_password_hash, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.old_password_hash = old_password_hash

    def validate_oldpassword(self, oldpassword):
        #check if the old password matches
        if not check_password_hash(self.old_password_hash, self.oldpassword.data):
                raise ValidationError('Old Password not correct')

class NewAccountForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'autocomplete': 'new-password'})
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=6, max=20), EqualTo('password')], 
                              render_kw={'autocomplete': 'new-password'})
    submit = SubmitField('Activate Account')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'autocomplete': 'new-password'})
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=6, max=20), EqualTo('password')],
                              render_kw={'autocomplete': 'new-password'})
    submit = SubmitField('Request Password Reset')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class EditGlauthForm(FlaskForm):
    debug = BooleanField('Debug Mode')
    ldap_enabled = BooleanField('Enable LDAP')
    ldap_listen = StringField('Address and Port', render_kw={"placeholder": "0.0.0.0:389"})
    ldaps_enabled = BooleanField('Enable LDAPS')
    ldaps_listen = StringField('Address and Port', render_kw={"placeholder": "0.0.0.0:636"})
    ldaps_cert = StringField('Certificate', render_kw={"placeholder": "/path/to/server.crt"}) # Required if ldaps_enabled
    ldaps_key = StringField('Key', render_kw={"placeholder": "/path/to/server.key"}) # Required if ldaps_enabled
    basedn = StringField('BaseDN', render_kw={"placeholder": "dc=glauth,dc=com"}) # Data Required
    nameformat = StringField('Name Format', render_kw={"placeholder": "cn"}, validators=[Length(max=4)],
                             description='Configure to customize dn format.')
    groupformat = StringField('Group Format', render_kw={"placeholder": "ou"}, validators=[Length(max=2)],
                             description='Configure to customize dn format.')
    sshkeyattr = StringField('SSH-Key Attribute', render_kw={"placeholder": "sshPublicKey"},
                             description='Configure ssh-key attribute name.')
    anonymousDSE = BooleanField('AnonymousDSE', description='Allow AnonymousDSE, useful for SSSD')
    submit = SubmitField('Save Settings')
    
    # Add Custom Validation, either ldap or ldaps must be enabled?