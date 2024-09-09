from flask import current_app
from itsdangerous import Serializer, BadSignature
from app.models import User


def generate_confirmation_token(user: User) -> str:
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps(user.username, salt="activate")


def confirm_token(token, expiration=3600) -> User | None:
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt="activate", max_age=expiration)
    except BadSignature:
        return None
    return User.query.filter_by(username=data).first_or_404()
