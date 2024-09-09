from flask import render_template, flash, redirect, url_for, request, render_template_string, current_app, Response
from flask_login import current_user
from werkzeug.exceptions import NotFound
from app.hello import hello
from app.hello.forms import HelloForm
from ..email import send_email
from ..models import User


@hello.route('/')
def get_hello():
    return {'answer': 'Hello World!'}, 200


@hello.route('/inline')
def get_inline():
    return render_template_string('<h1>Hello World!</h1>')


@hello.route('/greeting', methods=['GET', 'POST'])
def get_hello_name():
    form = HelloForm()
    if form.validate_on_submit():
        name = form.name.data
        flash(f'Hello {name}')
        return redirect(url_for('.get_index', name=name))
    return render_template('hello.html', form=form)


@hello.route('/index')
def get_index():
    name = request.args.get('name')
    return render_template('index.html', name=name)


@hello.route('/mail/<to>')
def get_mail(to):
    site = request.args.get('site') or 'Testapp'
    sender = request.args.get('sender')
    try:
        send_email(
            to=to,
            subject='Welcome',
            template='email/hello_mail',
            asynchronous=False,
            sender=sender,
            name='Nobody', site=site, link=request.root_url + url_for('hello.get_index'))
    except Exception as e:
        return Response(str(e), status=500)
    return Response("Mail sent", status=200)


@hello.route('/gravatar')
def get_gravatar():
    try:
        username = request.args.get('user')
        email = request.args.get('email')
        user: User
        if username:
            user = User.query.filter_by(username=username).first()
            if not user:
                raise NotFound("User not found")
        else:
            user = current_user
        print(user)
        return user.gravatar_icon(size=100, email=email, default='identicon')
    except Exception as e:
        return Response(str(e), status=500)
