from flask import render_template, flash, request, url_for, redirect, current_app
from flask_login import login_user, logout_user, current_user, login_required
from wtforms.validators import ValidationError
from . import auth
from app.auth.forms import LoginForm, RegistrationForm, VerifyAccountForm, AccountForm
from .. import db
from ..email import send_email
from ..models import User
from ..token import generate_confirmation_token, confirm_token
from ..utils import is_valid_email, is_valid_username


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        if not (is_valid_email(identifier) or is_valid_username(identifier)):
            raise ValidationError('Invalid email or username')
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_url = request.args.get('next')
            if next_url is None or not next_url.startswith('/'):
                next_url = url_for('main.index')
            print(next_url)
            return redirect(next_url)
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.login'))


@auth.route('/verify', methods=['GET', 'POST'])
def verify_account():
    form = VerifyAccountForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            send_email(
                to=user.email,
                subject='Welcome',
                template='email/hello_mail',
                asynchronous=True,
                name='Nobody', site='Flasky', link=request.root_url + url_for('main.index'))
            flash('Verification email sent')
        else:
            flash('Invalid username or password')
    return render_template('simple_form.html', title='Verify Account', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        name = form.name.data
        user = User(name=name)
        form.name.data = user.name
        if form.email.data == '':
            form.email.data = user.email
        if form.username.data == '':
            form.username.data = user.username
        if form.password.data == '':
            form.password.data = user.username
            form.confirm_password.data = user.username
    if form.validate_on_submit():
        user = User.authenticate_user(email=form.email.data,
                                      name=form.name.data,
                                      username=form.username.data,
                                      password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now login.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/account', methods=['GET', 'POST'])
def account():
    if not current_user.is_authenticated:
        raise ValidationError('Only logged in users can update their profile')
    user = User.query.filter_by(username=current_user.username).first()
    form = AccountForm()
    if request.method == 'GET':
        form.name.data = user.name
        form.username.data = user.username
        form.email.data = user.email
        form.gravatar.data = user.gravatar
        form.role.data = user.role
    if request.method == 'POST':
        if form.reset.data:
            current_app.logger.info('Reset current profile')
            form.email.data = user.generate_email()
            if user.confirmed:
                user.confirmed = False
                db.session.add(user)
                db.session.commit()
            if "," in form.name.data:
                names = form.name.data.split(',')
                if len(names) != 1:
                    if len(names) != 2:
                        raise ValueError('Name must be two words')
                    form.name.data = names[1].strip() + ' ' + names[0].strip()
            if not form.password.data:
                current_app.logger.info(f'Reset password to {user.username}')
                form.password.data = user.username
                form.confirm_password.data = user.username
        if form.submit.data:
            if form.validate_on_submit():
                if not user.confirmed:
                    token = generate_confirmation_token(user)
                    send_email(
                        to=user.email,
                        subject='Confirm your account',
                        template='email/confirm',
                        asynchronous=True,
                        user=user, token=token)
                    flash("Please check your email to confirm your account")
                form.populate_obj(user)
                db.session.add(user)
                db.session.commit()
                flash('Account updated successfully')
    return render_template('auth/account.html', title='Account', form=form, confirmed=user.confirmed)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    user = confirm_token(token)
    if user:
        if not user.confirmed:
            user.confirmed = True
            db.session.commit()
            current_app.logger.info(f'User {user.username} confirmed their account')
            flash('You have confirmed your account. Thanks!')
        else:
            flash('You have already confirmed your account.')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated and not current_user.confirmed and request.blueprint != 'auth' and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user)
    send_email(
        to=current_user.email,
        subject='Confirm Your Account',
        template='email/confirm',
        asynchronous=True,
        user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))
