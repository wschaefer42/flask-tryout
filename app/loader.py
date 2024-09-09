from sqlalchemy.orm import sessionmaker, lazyload, raiseload, joinedload

from . import db
from .models import User, Role


def load_users(delete_all: bool = False, update: bool = False):
    with db.session.begin():
        if delete_all:
            db.session.query(User).delete()
        added, updated = 0, 0
        Role.insert_roles()
        for name in ['Schäfer, Werner', 'Müller, Doris']:
            user = User(name)
            user.confirmed = True
            if add_user(user):
                added += 1
            elif update:
                if update_user(user):
                    updated += 1
        db.session.commit()
        print(f'Added {added}, updated {updated} users')


def add_user(user: User) -> bool:
    if db.session.query(User).filter(User.username == user.username).exists() is False:
        # if User.query.filter_by(username=user.username).first() is None:
        db.session.add(user)
        return True
    return False


def update_user(user: User) -> bool:
    existing_user = db.session.query(User).options(joinedload(User.role)).filter(User.username == user.username).first()
    if not existing_user == user:
        existing_user.name = user.name
        existing_user.birthday = user.birthday
        existing_user.password_hash = user.password_hash
        existing_user.email = user.email
        existing_user.confirmed = user.confirmed
        existing_user.role = user.role
        db.session.add(existing_user)
        return True
    return False
