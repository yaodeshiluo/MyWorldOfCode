from threading import Thread
from flask import current_app, render_template
from . import mail
from flask_mail import Message


def send_async_email(app,msg):
    '''
    app_ctx = app.app_context()
    app_ctx.push()
    current_app.name #'hello'
    app_ctx.pop()
    '''
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app,msg])
    thr.start()
    return thr # what for ??? can delete return???