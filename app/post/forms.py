from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, InputRequired
from app.models import Post


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    body_type = SelectField('Type', choices=Post.BodyType.items(), coerce=Post.BodyType.coerce)
    submit = SubmitField('Post')
    apply = SubmitField('Apply')

class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit')

