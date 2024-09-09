from random import randint

from faker import Faker
from flask import current_app
from app import db, trace
from app.models import User, Post


def _add_fake_users(count: int = 10):
    fake = Faker('de_CH')
    for i in range(count):
        name = f'{fake.last_name()}, {fake.first_name()}'
        user = User.create_user(
            name=name,
            confirmed=True,
            location=fake.city(),
            about_me=fake.text(max_nb_chars=100),
            member_since=fake.date_time_between(start_date='-1y', end_date='now'),
            gravatar=fake.email(),
            faked=True,
        )
        db.session.add(user)
        trace.debug(user)

def _add_fake_posts(count: int = 5):
    fake = Faker('de_CH')
    for user in User.query.filter_by(faked=True):
        for i in range(randint(0, count)):
            post = Post(body=fake.text(max_nb_chars=100), timestamp=fake.past_date(), author=user)
            db.session.add(post)
            trace.debug(post)

def add_fakes(test=True):
    with db.session.begin():
        trace.info(f'Adding fake data test-modus = {test}')
        _add_fake_users()
        _add_fake_posts()
        if not test:
            db.session.commit()
        else:
            db.session.rollback()

def delete_fakes(test=True):
    with db.session.begin():
        deleted = 0
        trace.info('Deleting fake data')
        for user in User.query.filter_by(faked=True):
            trace.debug(f'Deleting fake data for user {user}')
            db.session.delete(user)
            deleted += 1
        current_app.logger.info(f'Deleted {deleted} fake users')
        if not test:
            db.session.commit()
        else:
            db.session.rollback()
