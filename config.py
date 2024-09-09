import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[Flasky]'
    MAIL_DEFAULT_SENDER = 'Flasky Admin <flasky@example.com>'
    MAIL_MOCK_ADDRESS = 'flasky.{username}@mockinbox.com'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    @property
    def MAIL_ADDRESS(self):
        return self.MAIL_MOCK_ADDRESS

    @property
    def DEFAULT_LOGIN(self):
        return 'wernerschafer/wernerschafer'

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///data-dev.sqlite'
    DEBUG = True

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'
    TESTING = True

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URL') or 'sqlite:///data-prod.sqlite'

configurations: dict[str, (DevelopmentConfig, TestingConfig, ProductionConfig)] = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
