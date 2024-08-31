from flask import request, jsonify
from .auth import authenticate

# def protect_routes(app):
#   @app.before_request
#   def check_api_key():
#     print(request.headers)
#     if request.endpoint not in ['auth.login', 'auth.register', 'static']:
#       api_key = request.headers.get('x-api-key')
#       if not api_key or not authenticate(api_key):
#         return jsonify({'message': 'Unauthorized access'}), 401