from threading import Thread
from flask import render_template
from flask_mail import Message
from app import app, mail

# https://pythonhosted.org/Flask-Mail/

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_test_mail(address):
    send_email('[{}] TEST MAIL'.format(app.config['APPNAME']),
               sender=app.config['MAIL_ADMIN'],
               recipients=[address],
               text_body='Test email from {}'.format(app.config['APPNAME']))

def send_account_invite(user):
    token = user.get_new_account_token()
    send_email('[{}] Account created'.format(app.config['APPNAME']),
               sender=app.config['MAIL_ADMIN'],
               recipients=[user.mail],
               text_body=render_template('email/new_account.txt',
                                         user=user, token=token),
               html_body=render_template('email/new_account.html',
                                         user=user, token=token))

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[{}] Password Reset'.format(app.config['APPNAME']),
               sender=app.config['MAIL_ADMIN'],
               recipients=[user.mail],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))