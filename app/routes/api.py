from flask import Blueprint, request, jsonify
from datetime import datetime
import re
from app.utils.response import create_response
from app.utils.auth import require_auth
from app.services.scraper import SABDAScraper

api_bp = Blueprint('api', __name__)

# Initialize scraper
scraper = SABDAScraper()

@api_bp.route('/sabda', methods=['GET'])
@require_auth
def get_sabda_content():
    """API endpoint to get SABDA devotional content"""
    try:
        # Get query parameters
        year = request.args.get('year', type=int)
        date = request.args.get('date', type=str)
        
        # Validate parameters
        if not year:
            return jsonify(create_response(
                status="error",
                message="Year parameter is required (e.g., ?year=2025)"
            )), 400
            
        if not date:
            return jsonify(create_response(
                status="error",
                message="Date parameter is required in MMDD format (e.g., ?date=0902)"
            )), 400
        
        # Validate year range
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 1:
            return jsonify(create_response(
                status="error",
                message=f"Year must be between 2000 and {current_year + 1}"
            )), 400
        
        # Validate date format
        if not re.match(r'^\d{4}$', date):
            return jsonify(create_response(
                status="error",
                message="Date must be in MMDD format (e.g., 0902 for September 2nd)"
            )), 400
        
        # Scrape content
        result = scraper.scrape_sabda_content(year, date)
        
        # Add authentication info to metadata
        if result['status'] == 'success' and 'metadata' in result:
            result['metadata']['authenticated'] = True
            result['metadata']['auth_method'] = 'JWT'
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify(create_response(
            status="error",
            message=f"Server error: {str(e)}",
            metadata={"error_type": "ServerException"}
        )), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(create_response(
        status="success",
        message="Service is healthy",
        data={"service": "SABDA Scraper API"},
        metadata={"timestamp": datetime.now().isoformat()}
    ))
