from flask import Blueprint, jsonify
from datetime import datetime
from app.utils.response import create_response

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify(create_response(
        status="success",
        message="API documentation retrieved successfully",
        data={
            "service": "SABDA Scraper API",
            "version": "2.0.0",
            "endpoints": {
                "/api/auth/token": {
                    "method": "POST",
                    "description": "Generate authentication token",
                    "body": {
                        "api_key": "Your API key (string)"
                    },
                    "example": "POST with {\"api_key\": \"your_api_key\"}"
                },
                "/api/sabda": {
                    "method": "GET",
                    "description": "Get SABDA devotional content (requires authentication)",
                    "headers": {
                        "Authorization": "Bearer <token>"
                    },
                    "parameters": {
                        "year": "Year (integer, e.g., 2025)",
                        "date": "Date in MMDD format (string, e.g., '0902' for September 2nd)"
                    },
                    "example": "/api/sabda?year=2025&date=0902"
                },
                "/api/health": {
                    "method": "GET",
                    "description": "Health check endpoint"
                }
            },
            "authentication": {
                "type": "JWT Bearer Token",
                "flow": "1. POST /api/auth/token with api_key -> 2. Use returned token in Authorization header",
                "default_api_keys": {
                    "flutter_app": "sabda_flutter_2025_secure_key",
                    "mobile_app": "sabda_mobile_2025_secure_key"
                }
            }
        },
        metadata={
            "timestamp": datetime.now().isoformat(),
            "cors_enabled": True,
            "flutter_ready": True,
            "architecture": "modular"
        }
    ))
