from flask import Blueprint

hello = Blueprint('hello', __name__)

from app.hello import routes
