import jwt
import hashlib
from datetime import datetime
from functools import wraps
from flask import request, jsonify, current_app
from app.utils.response import create_response

def generate_token(api_key):
    """Generate JWT token for authenticated requests"""
    payload = {
        'api_key': hashlib.sha256(api_key.encode()).hexdigest(),
        'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify(create_response(
                status="error",
                message="Authorization header is required",
                metadata={"error_type": "AuthenticationError"}
            )), 401
        
        try:
            # Extract token from "Bearer <token>" format
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify(create_response(
                status="error",
                message="Invalid authorization header format. Use 'Bearer <token>'",
                metadata={"error_type": "AuthenticationError"}
            )), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify(create_response(
                status="error",
                message="Invalid or expired token",
                metadata={"error_type": "AuthenticationError"}
            )), 401
        
        request.user_payload = payload
        return f(*args, **kwargs)
    
    return decorated_function
