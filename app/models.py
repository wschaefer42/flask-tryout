import enum
import hashlib
from datetime import datetime, timedelta
import jwt
from flask import current_app, url_for
from flask_login import UserMixin
from slugify import slugify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from . import db, login_manager, config, moment, utils


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Follow(db.Model):
    __tablename__ = 'followers'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now())


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, index=True)
    username = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(100))
    birthday = db.Column(db.Date)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    role = db.relationship('Role')
    gravatar = db.Column(db.String(255), default=None, nullable=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    faked = db.Column(db.Boolean, default=False)
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration=3600):
        return jwt.encode(
            payload={"id": self.id, "exp": expiration},
            key=current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_auth_token(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return User.query.get(payload['id'])
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, Exception):
            return None

    def __init__(self, name: str, password: str = '', birthday: datetime = None):
        names = name.split(',')
        if len(names) != 1:
            if len(names) != 2 and len(names) != 3:
                raise ValueError('Name must be two words or three words (location)')
            self.name = names[1].strip() + ' ' + names[0].strip()
            self.email = f'{slugify(names[1])}.{slugify(names[0])}@example.com'
            self.username = f'{slugify(names[1])}{slugify(names[0])}'
            if len(names) == 3:
                self.location = names[2].strip()
            if not password:
                password = names[1].strip().lower()
        elif len(names) == 1:
            self.email = names[0] + '@example.com'
            self.username = slugify(names[0])
            if not password:
                password = names[0].strip().lower()
            self.name = name
        self.birthday = birthday
        self.member_since = (datetime.today() - timedelta(days=2)).date()
        self.password = password
        if config.MAIL_ADDRESS:
            current_app.logger.info('MAIL_MOCK_ADDRESS=' + config.MAIL_ADDRESS)
            self.email = config.MAIL_ADDRESS.format(username=self.username)
        if self.role is None:
            if self.username == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(default=True).first()

    def generate_email(self, overwrite=False) -> str:
        if config.MAIL_ADDRESS:
            return config.MAIL_ADDRESS.format(username=self.username)
        else:
            if overwrite or not self.email:
                return f'{self.username}@example.com'
            else:
                return self.email

    def can(self, permissions):
        return self.role is not None and self.role.has_permission(permissions)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def gravatar_icon(self, email=None, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        email = email or self.gravatar or self.email
        hashcode = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hashcode, size=size, default=default, rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    # let's use @classmethod to define a constructor for a anonymous user
    @classmethod
    def anonymous_user(cls, password: str):
        return cls(name='nobody', password=password)

    @classmethod
    def create_user(cls, **kwargs):
        name = kwargs.get('name')
        password = kwargs.get('password')
        user = cls(name=name, password=password)
        for k, v in kwargs.items():
            if k != 'password' and k != 'name':
                setattr(user, k, v)
        if user.role is None:
            user.role = Role.query.filter_by(default=True).first()
        return user

    @classmethod
    def authenticate_user(cls, email: str, name: str, username: str, password: str):
        u = cls(name, password)
        u.email = email
        u.name = name
        u.username = username
        u.password = password
        return u

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    @property
    def myself_posts(self):
        return Post.query.filter_by(author_id=self.id)

    def to_json(self):
        return {
            'id': self.id,
            'url': (self.id and url_for('api.get_user', user_id=self.id)) or None,
            'name': self.name,
            'location': self.location,
            'email': self.email,
            'username': self.username,
            'member_since': self.member_since,
            'post_count': self.posts.count(),
        }

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def __eq__(self, other):
        return (isinstance(other, User)
                and self.username == other.username
                and self.email == other.email
                and self.birthday == other.birthday
                and self.password_hash == other.password_hash)

    def __str__(self):
        return '<User {} {} {} in {} {}>'.format(self.id, self.username, self.name, self.location, self.email)


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    # users = db.relationship('User', backref='role', lazy='joined')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def add_permissions(self, perms: [Permission]):
        for perm in perms:
            self.add_permission(perm)

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        with db.session.begin_nested() as savepoint:
            roles = {
                'User':
                    [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
                'Moderator':
                    [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE],
                'Administrator':
                    [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE, Permission.ADMIN],
            }
            default_role = 'User'
            for r in roles:
                role = Role.query.filter_by(name=r).first()
                if role is None:
                    role = Role(name=r)
                role.reset_permissions()
                role.add_permissions(roles[r])
                role.default = (role.name == default_role)
                db.session.add(role)
            savepoint.commit()
            # db.session.commit()


class Post(db.Model):
    class BodyType(enum.Enum):
        MARKDOWN = 'markdown'
        HTML = 'html'
        TEXT = 'text'

        @classmethod
        def items(cls):
            return [(e, e.value) for e in cls]

        @classmethod
        def values(cls):
            return (e.value for e in cls)

        @classmethod
        def coerce(cls, item):
            print(cls, item, type(item))
            if isinstance(item, cls):
                return item
            try:
                if isinstance(item, str):
                    for e in cls:
                        if item == e.__str__():
                            return e
                return Post.BodyType[item]
            except Exception as e:
                print('could not coerce {}, error {}'.format(item, e))
                raise ValueError(item)

    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_type = db.Column(db.Enum(BodyType, values_callable=lambda obj: [item.value for item in obj], ))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def __str__(self):
        return '<Post {}, {}, {}>'.format(self.author.username, self.body, self.timestamp.strftime('%d.%m.%Y'))

    @staticmethod
    def on_changed_body(target, value, old_value, initiator):
        target.body = utils.sanitize_html(value)


# db.event.listen(Post.body, 'set', Post.on_changed_body)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
    disabled = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
