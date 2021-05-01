from flask import render_template, flash, redirect, url_for, request, abort, Response
from app import app, db
from app.forms import LoginForm, EditProfileForm, ChangePasswordForm 
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, NewAccountForm
from app.forms import TestMailForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Group
from app.email import send_password_reset_email, send_test_mail
from werkzeug.urls import url_parse
from app.glauth import create_glauth_config

@app.route('/')
@app.route('/index')
@login_required
def index():
    pgroup_name = Group.query.filter_by(unixid=current_user.primarygroup).first().name
    #return render_template('index.html', title='Home', user=user)
    return render_template("index.html", title='Home Page', primarygroup=pgroup_name)

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

    form = LoginForm()
    if form.validate_on_submit():
        #flash('Login requested for user {} with pw {}, remember_me={}'.format(
        #    form.username.data, form.password.data, form.remember_me.data))
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        elif user is not None and (user.is_active == False):
            flash('Account has been disabled, contact Administrator.')
            return redirect(url_for('login'))
        elif user is not None and (user.mail == None or ''):
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
    if form.validate_on_submit():
        current_user.givenname = form.givenname.data
        current_user.surname = form.surname.data
        current_user.mail = form.mail.data
        db.session.commit()
        create_glauth_config()
        flash('Your changes have been saved.')
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
    if form.validate_on_submit():
        current_user.set_password(form.newpassword1.data)
        db.session.commit()
        create_glauth_config()
        flash('Your password has been changed.')
        return redirect(url_for('index'))
    return render_template('change_password.html', form=form)

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
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_active = True
        db.session.commit()
        create_glauth_config()
        flash('Your password has been reset, please login.')
        return redirect(url_for('login'))
    fullname = '{}'.format(user.givenname + ' ' + user.surname)
    return render_template('reset_password.html', form=form, fullname=fullname)

@app.route('/new_account/<token>', methods=['GET', 'POST'])
def new_account(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_new_account_token(token)
    if not user:
        return redirect(url_for('index'))
    form = NewAccountForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_active = True
        db.session.commit()
        create_glauth_config()
        flash('Your password has been set, please login.')
        return redirect(url_for('login'))
    fullname = '{}'.format(user.givenname + ' ' + user.surname)
    return render_template('new_account.html', form=form, fullname=fullname)

import base64

@app.route('/forward_auth/header/', methods=['GET', 'POST'], subdomain="<subdomain>")
def forward_auth(subdomain):
    """The actual login is handled by flask_login
    """
    protocol = request.headers.get('X-Forwarded-Proto')
    host = request.headers.get('X-Forwarded-Host')
    uri = request.headers.get('X-Forwarded-Uri')
    origin = protocol+"://"+host+uri
    method = request.headers.get('X-Forwarded-Method')

    #Whitelist based on IP address
    sourceIp=request.headers.get('X-Forwarded-For',None)
    if sourceIp in request.args.getlist('ip'):
        return "", 201

    if current_user.is_anonymous:
        return Response(
            f'Could not verify your access level for that {origin}.\n'
            'You have to login with proper credentials\n', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    allowed_groups = request.args.getlist('group')
    if current_user.in_groups(*allowed_groups):
        return "", 201

    return abort(403)

#@app.route('/forward_auth/cookie/', methods=['GET', 'POST'], subdomain="<subdomain>")
def forward_auth(subdomain):
    """Unfortunatly implementing the CORS cookies in a clean way behind traefik is a bit beyond
    me. There are things traefik could do to make this easier, like allow me to do a post
    request to the auth server from behind the proxy, but alas.
    """
    raise NotImplementedError
    protocol = request.headers.get('X-Forwarded-Proto')
    host = request.headers.get('X-Forwarded-Host')
    uri = request.headers.get('X-Forwarded-Uri')
    origin = protocol+"://"+host+uri
    method = request.headers.get('X-Forwarded-Method')

    #Whitelist based on IP address, wish there was some way to whitelist based on
    # docker service name. Maybe traefik will do something about it.
    #ToDo: If somone wants maybe add IP range whitelisting? I just did this because it
    # was very easy to do, and someone might find it useful.
    sourceIp=request.headers.get('X-Forwarded-For',None)
    if sourceIp in request.args.getlist('ip'):
        return "", 201

    if current_user.is_anonymous:
        return render_template('forward_auth.html'), 401
        loginpage = login(internal_redirect=origin)
        if type(loginpage)==str:
            return loginpage, 401
        return loginpage

    #Simple no DB based group lookup, configurable via client env variable
    #Makes sure the user is in one of the groups passed as a `group` querystring arg.
    allowed_groups = request.args.getlist('group')
    if current_user.in_groups(*allowed_groups):
        return "", 201

    return abort(401)
