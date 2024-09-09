from flask import request, current_app, jsonify, make_response
from werkzeug.exceptions import BadRequest
from app import db
from . import api
from ..models import User

@api.route('/users', methods=['POST'])
def add_user():
    name = request.args.get('name')
    if not name:
        raise BadRequest('Name is required')
    test = request.args.get('test') == "true"
    user = User(name=name)
    if User.query.filter_by(username=user.username).first() is not None:
        return make_response('User already exists', 409)
    current_app.logger.info(f'Creating user {user}')
    if not test:
        db.session.add(user)
        db.session.commit()
    return jsonify(user.to_json())

@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_json())

@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return f'Deleted user {user.name}'
