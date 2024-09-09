import os
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from app import mail


def send_async_email(app, msg):
    app.trace.info(f'Sending email to {msg.recipients}')
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, asynchronous=False, sender=None, **kwargs):
    app = current_app
    msg = Message(
        subject=app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        recipients=[to],
    )
    if sender is not None:
        msg.sender = sender
    msg.body = render_template(template + '.txt', **kwargs)
    if os.path.exists(os.path.join(app.template_folder, template + '.html')):
        msg.html = render_template(template + '.html', **kwargs)
    if not asynchronous:
        with app.app_context():
            mail.send(msg)
    else:
        Thread(target=send_async_email(app, msg)).start()
    # Thread(target=send_async_email, args=(app, msg)).start()
    # thr.start()
    # return thr
