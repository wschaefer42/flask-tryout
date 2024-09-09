from flask import jsonify

def _make_response(message, error, status_code):
    response = jsonify({'error': error, 'message': message})
    response.code = status_code
    return response

def bad_request(message):
    return _make_response(message, 'Bad Request', 400)

def unauthorized(message):
    return _make_response(message, 'Unauthorized', 401)

def forbidden(message):
    return _make_response(message, 'Forbidden', 403)
