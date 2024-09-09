from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class HelloForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    language = StringField('Your Language', validators=[DataRequired()], default='de')
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
