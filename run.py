import logging
import os
import click
from flask_migrate import Migrate
from app import create_app, db, config, login_manager, trace
from app.fake import add_fakes, delete_fakes
from app.models import User
from app.loader import load_users
from dotenv import load_dotenv

load_dotenv()
app = create_app(os.getenv('FLASK_CONFIG') or 'development')
app.app_context().push()
migrate = Migrate(app, db)

@login_manager.request_loader
def load_user_from_request(request):
    if config.DEFAULT_LOGIN:
        username_passwords = config.DEFAULT_LOGIN.split('/')
        if len(username_passwords) != 2:
            raise ValueError('Wrong username/password combination.')
        user = User.query.filter_by(username=username_passwords[0]).first()
        if user is not None and user.verify_password(password=username_passwords[1]):
            trace.info(f'Logged in as {user.username}')
            return user
    return None

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

@app.route('/test')
def get_test():
    return 'Hello Test!'

@app.cli.command('load-data', help='Load test data into database')
@click.option('--update', is_flag=True,  help='Update data')
@click.option('--delete_all', is_flag=True, help='Delete all data')
def load_data(update=False, delete_all=False):
    load_users(delete_all, update)

@app.cli.command('fakes', help='Manage fake data')
@click.option('--add', is_flag=True, help='Add fake data')
@click.option('--delete', is_flag=True, help='Delete fake data')
@click.option('--test', is_flag=True, help='Test fake operation', default=False)
@click.option('--debug', is_flag=True, help='Debug mode', default=False)
def fakes(add, delete, test, debug):
    trace.setLevel(logging.INFO)
    if debug:
        trace.setLevel(logging.DEBUG)
        pass
    trace.debug(f'add={add}, delete={delete}, test={test}')
    if add:
        add_fakes(test)
    if delete:
        delete_fakes(test)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    app.run()