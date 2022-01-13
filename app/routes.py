from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import LoginForm, EditProfileForm, ChangePasswordForm 
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, NewAccountForm
from app.forms import TestMailForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Group
from app.email import send_password_reset_email, send_test_mail
from werkzeug.urls import url_parse
from app.glauth import create_glauth_config
from ipaddress import ip_network, ip_address

@app.route('/')
@app.route('/index')
@login_required
def index():
    pgroup_name = Group.query.filter_by(gidnumber=current_user.primarygroup).first().name
    #return render_template('index.html', title='Home', user=user)
    return render_template("index.html", title='Profile', primarygroup=pgroup_name)

@app.route('/testmail', methods=['GET', 'POST'])
@login_required
def testmail():
    # secure with only admin
    if not current_user.is_admin:
        abort(403)
    form = TestMailForm()
    if form.validate_on_submit():
        send_test_mail(form.mail.data)
        flash('Test mail send to {}'.format(form.mail.data))
        return redirect(url_for('index'))
    return render_template('testmail.html', title='TEST MAIL', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if 'X-Forwarded-For' in request.headers:
        remote_addr = request.headers.get('X-Forwarded-For',None)
    else:
        remote_addr = request.remote_addr or 'untrackable'

    form = LoginForm() 
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            app.logger.warning('Failed login attempt with user {} from {}'.format(
                form.username.data, 
                str(remote_addr)))
            return redirect(url_for('login'))
        elif user is not None and (user.is_active == False):
            flash('Account has been disabled, contact Administrator.')
            return redirect(url_for('login'))
        elif user is not None and (user.mail is None or user.mail==''):
            flash('Account not eligable to login.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':    
            return redirect(url_for('index'))
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.mail)
    if form.cancel.data:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        current_user.givenname = form.givenname.data
        current_user.surname = form.surname.data
        current_user.mail = form.mail.data
        db.session.commit()
        try:
            create_glauth_config()
            flash('Your changes have been saved.')
        except Exception as exc:
            flash('Your changes were not saved: ' + str(exc))
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.givenname.data = current_user.givenname
        form.surname.data = current_user.surname
        form.mail.data = current_user.mail
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

# Password Change Form
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(current_user.password_hash)
    if form.cancel.data:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        current_user.set_password(form.newpassword1.data)
        db.session.commit()
        try:
            create_glauth_config()
            flash('Your password has been changed.')
        except Exception as exc:
            flash('Your password was not changed: ' + str(exc))
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.oldpassword.data = ""
        form.newpassword1.data = current_user.surname
        form.newpassword2.data = current_user.mail
    return render_template('change_password.html', title='Change Password', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(mail=form.email.data).first()
        # Inactive Users can't change their password!
        if user and user.is_active:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_active = True
        db.session.commit()
        try:
            create_glauth_config()
            flash('Your password has been reset, please login.')
        except Exception as exc:
            flash('Your password was not reset: ' + str(exc))
        return redirect(url_for('login'))
    fullname = '{}'.format(user.givenname + ' ' + user.surname)
    return render_template('reset_password.html', form=form, fullname=fullname)

@app.route('/new_account/<token>', methods=['GET', 'POST'])
def new_account(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_new_account_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = NewAccountForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_active = True
        db.session.commit()
        try:
            create_glauth_config()
            flash('Your password has been set, please login.')
        except Exception as exc:
            flash('Your password was not set: ' + str(exc))
        return redirect(url_for('login'))
    fullname = '{}'.format(user.givenname + ' ' + user.surname)
    return render_template('new_account.html', title='Activate Account', form=form, fullname=fullname)

@app.route('/forward_auth/header/', methods=['GET', 'POST'])
def forward_auth():
    """The actual login is handled by flask_login
    """
    protocol = request.headers.get('X-Forwarded-Proto')
    host = request.headers.get('X-Forwarded-Host')
    uri = request.headers.get('X-Forwarded-Uri')

    #Whitelist based on IP address
    sourceIp=request.headers.get('X-Forwarded-For',None)     
    if sourceIp in request.args.getlist('ip'):
        return "", 201

    #Whitelist based on CIDR netmask
    for net in request.args.getlist('network'):
        net = ip_network(net)
        if sourceIp and ip_address(sourceIp) in net:
            return "", 201

    if current_user.is_anonymous:
        return "", 401
            
    allowed_groups = request.args.getlist('group')
    if current_user.is_authenticated:
        if allowed_groups:
            if current_user.in_groups(*allowed_groups):
                return "", 201
        else:    
            return "", 201
    
    return "", 403

@app.route('/forward_auth/forbidden')
def not_allowed():
    origin = request.args.get('from')
    return render_template('forbidden.html', origin=origin), 403