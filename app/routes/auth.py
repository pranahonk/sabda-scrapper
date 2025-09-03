from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.utils.response import create_response
from app.utils.auth import generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/token', methods=['POST'])
def get_auth_token():
    """Generate authentication token for Flutter app"""
    try:
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify(create_response(
                status="error",
                message="API key is required in request body",
                metadata={"error_type": "AuthenticationError"}
            )), 400
        
        api_key = data['api_key']
        
        # Validate API key
        if api_key not in current_app.config['API_KEYS'].values():
            return jsonify(create_response(
                status="error",
                message="Invalid API key",
                metadata={"error_type": "AuthenticationError"}
            )), 401
        
        # Generate token
        token = generate_token(api_key)
        
        return jsonify(create_response(
            status="success",
            message="Token generated successfully",
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_in": int(current_app.config['JWT_EXPIRATION_DELTA'].total_seconds())
            },
            metadata={
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']).isoformat()
            }
        )), 200
        
    except Exception as e:
        return jsonify(create_response(
            status="error",
            message=f"Token generation failed: {str(e)}",
            metadata={"error_type": "ServerException"}
        )), 500
