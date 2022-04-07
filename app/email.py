from threading import Thread
from flask import render_template
from flask_mailman import EmailMultiAlternatives

from app import app
from config import Config

def send_async_email(_app, msg):
    with _app.app_context():
        msg.send(fail_silently=False)

def send_email(subject, sender, recipients, text_body, html_body=None):
    msg = EmailMultiAlternatives(subject, text_body, from_email=sender, to=recipients)
    if html_body:
        msg.attach_alternative(html_body, 'text/html')
    Thread(target=send_async_email, args=(app, msg)).start()

def send_test_mail(address):
    send_email('[{}] TEST MAIL'.format(Config.APPNAME),
               sender=Config.MAIL_ADMIN,
               recipients=[address],
               text_body='Test email from {}'.format(Config.APPNAME))

def send_account_invite(user):
    token = user.get_new_account_token()
    send_email('[{}] Account created'.format(Config.APPNAME),
               sender=Config.MAIL_ADMIN,
               recipients=[user.mail],
               text_body=render_template('email/new_account.txt',
                                         user=user, token=token),
               html_body=render_template('email/new_account.html',
                                         user=user, token=token))

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[{}] Password Reset'.format(Config.APPNAME),
               sender=Config.MAIL_ADMIN,
               recipients=[user.mail],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))