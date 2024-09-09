from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Email, DataRequired, Length, Regexp, EqualTo, ValidationError, InputRequired
from wtforms.widgets.core import PasswordInput
from wtforms_sqlalchemy.fields import QuerySelectField

from app import db
from app.models import User, Role


class LoginForm(FlaskForm):
    identifier = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class VerifyAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_account = BooleanField('Confirm Account', validators=[DataRequired()])
    submit = SubmitField('Confirm Account')

    def validate_username(self, field):
        if field.data != "":
            user = User.query.filter_by(username=field.data).first()
            if user is None or not user.verify_password(self.password.data):
                raise ValidationError('Invalid Account')

class UserBaseForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    name = StringField('Name', description="Lastname, Firstname", validators=[
        InputRequired(),
        Regexp('^[A-ÄÖÜ][A-Za-zäöüéàèÄÖÜ]+[ ]+[A-Za-z][A-Za-zäöüéàèÄÖÜ\' ]+$', 0, 'Invalid name format'),
        Length(4, 100)])
    username = StringField('Username', validators=[
        Length(min=3, max=64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Invalid username format')
    ])
    gender = SelectField(
        'Gender',
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        default='M')
    password = StringField('Password', validators=[Length(min=8, max=25)], widget=PasswordInput(hide_value=False))
    confirm_password = StringField('Confirm Password', validators=[EqualTo('password')], widget=PasswordInput(hide_value=False))
    gravatar = StringField('Gravatar', validators=[Email()])
    role = QuerySelectField('Role', query_factory=lambda: Role.query.all(), get_label='name')


class AccountForm(UserBaseForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username.render_kw = {'readonly': True, 'style': 'background-color: lightgrey'}
    submit = SubmitField('Update')
    reset = SubmitField('Reset')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    name = StringField('Name', description="Lastname, Firstname", validators=[
        InputRequired(),
        Regexp('^[A-ÄÖÜ][A-Za-zäöüéàèÄÖÜ]+[ ]+[A-Za-z][A-Za-zäöüéàèÄÖÜ\' ]+$', 0, 'Invalid name format'),
        Length(4, 100)])
    username = StringField('Username', validators=[
        Length(min=3, max=64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Invalid username format')
    ])
    gender = SelectField(
        'Gender',
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        default='M')
    password = PasswordField('Password', validators=[Length(min=8, max=25)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    confirm_account = BooleanField('Confirm Account')
    submit = SubmitField('Register')

    @staticmethod
    def validate_email(form, field):
        if field.data != "":
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('Email already registered.')

    @staticmethod
    def validate_username(form, field):
        if field.data != "":
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('Username already registered.')
