from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import random
from fake_useragent import UserAgent
import cloudscraper
from flask_cors import CORS
import jwt
import os
from functools import wraps
import hashlib
import secrets

app = Flask(__name__)
CORS(app, origins=["*"], methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)

# API Keys for authentication
API_KEYS = {
    'flutter_app': os.environ.get('FLUTTER_API_KEY', 'sabda_flutter_2025_secure_key'),
    'mobile_app': os.environ.get('MOBILE_API_KEY', 'sabda_mobile_2025_secure_key')
}

def create_response(status="success", message="", data=None, metadata=None):
    """Create standardized API response"""
    response = {
        "status": status,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata is not None:
        response["metadata"] = metadata
    
    return response

def generate_token(api_key):
    """Generate JWT token for authenticated requests"""
    payload = {
        'api_key': hashlib.sha256(api_key.encode()).hexdigest(),
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
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

class SABDAScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.ua = UserAgent()
        
    def get_random_headers(self):
        """Generate random headers to avoid bot detection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def scrape_sabda_content(self, year, date):
        """Scrape content from SABDA website with anti-bot measures"""
        try:
            # Format the date parameter (MMDD format)
            formatted_date = date.zfill(4)
            
            # Construct URL
            url = f"https://www.sabda.org/publikasi/e-sh/cetak/?tahun={year}&edisi={formatted_date}"
            
            # Add random delay to avoid being detected as bot
            time.sleep(random.uniform(2, 5))
            
            # Make request with cloudscraper (bypasses Cloudflare)
            response = self.scraper.get(url, headers=self.get_random_headers(), timeout=15)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # Extract content
            content_data = self.extract_content(soup, url)
            
            return create_response(
                status="success",
                message="Content scraped successfully",
                data=content_data,
                metadata={
                    "url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "SABDA.org"
                }
            )
            
        except requests.exceptions.RequestException as e:
            return create_response(
                status="error",
                message=f"Request failed: {str(e)}",
                metadata={
                    "url": url if 'url' in locals() else None,
                    "error_type": "RequestException"
                }
            )
        except Exception as e:
            return create_response(
                status="error",
                message=f"Scraping failed: {str(e)}",
                metadata={
                    "url": url if 'url' in locals() else None,
                    "error_type": "GeneralException"
                }
            )
    
    def extract_content(self, soup, url):
        """Extract and structure content from the parsed HTML"""
        content = {}
        
        # Extract title
        title_tag = soup.find('title')
        content['title'] = title_tag.text.strip() if title_tag else None
        
        # Get all text content
        main_text = soup.get_text()
        
        # Clean up the text
        lines = [line.strip() for line in main_text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Extract scripture reference (pattern like "Lukas 13:18-21")
        scripture_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)', clean_text)
        content['scripture_reference'] = scripture_match.group(1) if scripture_match else None
        
        # Extract devotional title (usually after scripture reference)
        title_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)(.+?)(?=\n|$)', clean_text)
        if title_match:
            devotional_title = title_match.group(2).strip()
            # Remove any links or extra formatting
            devotional_title = re.sub(r'\[.*?\]', '', devotional_title).strip()
            content['devotional_title'] = devotional_title
        
        # Extract main devotional content (paragraphs between scripture and footer)
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            # Skip header/navigation elements
            if any(skip in line.lower() for skip in ['sabda.org', 'publikasi', 'versi cetak', 'http://', 'https://']):
                continue
            
            # Skip footer elements
            if any(footer in line.lower() for footer in ['yayasan lembaga sabda', 'webmaster@', 'ylsa.org']):
                break
                
            # If line looks like a paragraph content
            if len(line) > 20 and not line.startswith('[') and not line.endswith(']'):
                current_paragraph.append(line)
            elif current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # Add last paragraph if exists
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        content['devotional_content'] = paragraphs
        content['full_text'] = clean_text
        content['word_count'] = len(clean_text.split())
        
        return content

# Initialize scraper
scraper = SABDAScraper()

@app.route('/api/sabda', methods=['GET'])
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

@app.route('/api/auth/token', methods=['POST'])
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
        if api_key not in API_KEYS.values():
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
                "expires_in": int(app.config['JWT_EXPIRATION_DELTA'].total_seconds())
            },
            metadata={
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']).isoformat()
            }
        )), 200
        
    except Exception as e:
        return jsonify(create_response(
            status="error",
            message=f"Token generation failed: {str(e)}",
            metadata={"error_type": "ServerException"}
        )), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(create_response(
        status="success",
        message="Service is healthy",
        data={"service": "SABDA Scraper API"},
        metadata={"timestamp": datetime.now().isoformat()}
    ))

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify(create_response(
        status="success",
        message="API documentation retrieved successfully",
        data={
            "service": "SABDA Scraper API",
            "version": "1.0.0",
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
            "flutter_ready": True
        }
    ))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
