import os
import re
import time
import random
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from typing import Dict, List, Optional, Tuple, Any, Union

import jwt
import requests
import cloudscraper
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORS configuration - more restrictive in production
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, methods=["GET", "POST", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization"])

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=int(os.environ.get('JWT_EXPIRATION_HOURS', '24')))
app.config['CACHE_TTL'] = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hour default
app.config['MAX_REQUESTS_PER_MINUTE'] = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '60'))

# API Keys for authentication
API_KEYS = {
    'flutter_app': os.environ.get('FLUTTER_API_KEY', 'sabda_flutter_2025_secure_key'),
    'mobile_app': os.environ.get('MOBILE_API_KEY', 'sabda_mobile_2025_secure_key')
}

# Simple in-memory cache for scraped content
content_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
request_counts: Dict[str, List[datetime]] = {}

def create_response(status: str = "success", message: str = "", 
                   data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized API response with type hints"""
    response = {
        "status": status,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata is not None:
        response["metadata"] = metadata
    
    return response

def get_client_ip() -> str:
    """Get client IP address handling proxy headers"""
    return (request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown').split(',')[0].strip()

def rate_limit_check(client_ip: str) -> bool:
    """Simple rate limiting check"""
    now = datetime.now()
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    
    # Clean old requests (older than 1 minute)
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] 
                                if (now - req_time).total_seconds() < 60]
    
    # Check if limit exceeded
    if len(request_counts[client_ip]) >= app.config['MAX_REQUESTS_PER_MINUTE']:
        return False
    
    request_counts[client_ip].append(now)
    return True

def get_cached_content(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached content if still valid"""
    if cache_key in content_cache:
        content, timestamp = content_cache[cache_key]
        if (datetime.now() - timestamp).total_seconds() < app.config['CACHE_TTL']:
            logger.info(f"Cache hit for key: {cache_key}")
            return content
        else:
            # Remove expired cache
            del content_cache[cache_key]
    return None

def set_cached_content(cache_key: str, content: Dict[str, Any]) -> None:
    """Set content in cache"""
    content_cache[cache_key] = (content, datetime.now())
    logger.info(f"Content cached for key: {cache_key}")

@lru_cache(maxsize=128)
def generate_token(api_key: str) -> str:
    """Generate JWT token for authenticated requests with caching"""
    payload = {
        'api_key': hashlib.sha256(api_key.encode()).hexdigest(),
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token with better error handling"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token from IP: {get_client_ip()}")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token from IP: {get_client_ip()}, error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

def require_auth(f):
    """Decorator to require authentication with rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        # Rate limiting check
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify(create_response(
                status="error",
                message="Rate limit exceeded. Please try again later.",
                metadata={"error_type": "RateLimitError"}
            )), 429
        
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning(f"Missing auth header from IP: {client_ip}")
            return jsonify(create_response(
                status="error",
                message="Authorization header is required",
                metadata={"error_type": "AuthenticationError"}
            )), 401
        
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            logger.warning(f"Invalid auth header format from IP: {client_ip}")
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
        
        g.user_payload = payload
        return f(*args, **kwargs)
    
    return decorated_function

class SABDAScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.ua = UserAgent()
        self.session_timeout = 30
        
    @lru_cache(maxsize=10)
    def get_random_headers(self, seed: int = None) -> Dict[str, str]:
        """Generate random headers with caching for better performance"""
        if seed:
            random.seed(seed)
        
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
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
    
    def scrape_sabda_content(self, year: int, date: str) -> Dict[str, Any]:
        """Scrape content from SABDA website with caching and optimizations"""
        formatted_date = date.zfill(4)
        cache_key = f"sabda_{year}_{formatted_date}"
        url = None
        
        try:
            # Check cache first
            cached_result = get_cached_content(cache_key)
            if cached_result:
                return create_response(
                    status="success",
                    message="Content retrieved from cache",
                    data=cached_result,
                    metadata={
                        "url": f"https://www.sabda.org/publikasi/e-sh/cetak/?tahun={year}&edisi={formatted_date}",
                        "cached": True,
                        "source": "SABDA.org"
                    }
                )
            
            # Construct URL
            url = f"https://www.sabda.org/publikasi/e-sh/cetak/?tahun={year}&edisi={formatted_date}"
            logger.info(f"Scraping URL: {url}")
            
            # Reduced delay range for better performance
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            # Make request with better timeout and error handling
            response = self.scraper.get(
                url, 
                headers=self.get_random_headers(hash(cache_key) % 100),
                timeout=self.session_timeout
            )
            response.raise_for_status()
            
            # Validate response content
            if not response.content or len(response.content) < 100:
                raise ValueError("Received empty or too short response")
            
            # Parse HTML content with faster parser
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract content
            content_data = self.extract_content(soup, url)
            
            # Cache the result
            set_cached_content(cache_key, content_data)
            
            result = create_response(
                status="success",
                message="Content scraped successfully",
                data=content_data,
                metadata={
                    "url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "SABDA.org",
                    "cached": False,
                    "delay_used": delay
                }
            )
            
            logger.info(f"Successfully scraped content for {year}-{formatted_date}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping {url}")
            return create_response(
                status="error",
                message="Request timeout. The server took too long to respond.",
                metadata={
                    "url": url,
                    "error_type": "TimeoutException"
                }
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return create_response(
                status="error",
                message=f"Request failed: {str(e)}",
                metadata={
                    "url": url,
                    "error_type": "RequestException"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {str(e)}")
            return create_response(
                status="error",
                message=f"Scraping failed: {str(e)}",
                metadata={
                    "url": url,
                    "error_type": "GeneralException"
                }
            )
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract and structure content with proper paragraph separation"""
        content = {}
        
        # Extract title with fallback
        title_tag = soup.find('title')
        content['title'] = title_tag.get_text(strip=True) if title_tag else "SABDA Devotional"
        
        # Find the main content area
        main_content = soup.find('td', class_='wj') or soup.find('body') or soup
        
        # Get all text for basic extraction
        all_text = main_content.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Pre-compile regex patterns
        scripture_pattern = re.compile(r'\b([A-Za-z]+\s+\d+:\d+(?:-\d+)?)\b')
        donation_pattern = re.compile(r'mari memberkati.*?pancar pijar alkitab|bca\s*106\.30066\.22', re.IGNORECASE | re.DOTALL)
        
        # Extract scripture reference
        scripture_match = scripture_pattern.search(clean_text)
        content['scripture_reference'] = scripture_match.group(1) if scripture_match else None
        
        # Extract devotional title (look for text after scripture reference)
        devotional_title = None
        if scripture_match:
            title_start = scripture_match.end()
            # Find the title which is typically on the same line or next line after scripture
            remaining_text = clean_text[title_start:]
            lines_after_scripture = remaining_text.split('\n')
            
            for line in lines_after_scripture[:3]:  # Check first 3 lines
                line = line.strip()
                if line and len(line) > 5 and not line.lower().startswith('ketika'):
                    # Clean up the title
                    devotional_title = re.sub(r'\[.*?\]|\s{2,}', ' ', line).strip()
                    break
        
        content['devotional_title'] = devotional_title
        
        # Extract paragraphs - try HTML parsing first
        paragraphs = []
        p_tags = main_content.find_all('p')
        
        for p_tag in p_tags:
            # Skip empty paragraphs or those with only &nbsp;
            if not p_tag.get_text(strip=True) or p_tag.get_text(strip=True) == '\xa0':
                continue
            
            # Skip paragraphs with center alignment (donation text)
            if p_tag.get('align') == 'center':
                continue
                
            # Get paragraph text
            paragraph_text = p_tag.get_text(strip=True)
            
            # Skip if contains donation/footer patterns
            if donation_pattern.search(paragraph_text):
                continue
                
            footer_patterns = [
                'yayasan lembaga sabda', 'webmaster@', 'ylsa.org', 
                'copyright', '© ', 'pancar pijar alkitab', 'bca 106.30066.22',
                'mari memberkati', 'santapan harian', 'halaman ini adalah versi'
            ]
            
            if any(pattern in paragraph_text.lower() for pattern in footer_patterns):
                continue
            
            # Skip very short paragraphs
            if len(paragraph_text) < 50:
                continue
                
            # Clean and add paragraph
            paragraph_text = re.sub(r'\s{2,}', ' ', paragraph_text).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)
        
        # If HTML parsing didn't work well, use text-based approach
        if len(paragraphs) <= 1:
            logger.info(f"Using text-based paragraph extraction for {url}")
            paragraphs = []
            
            # Remove header and footer content first
            text_lines = []
            found_content_start = False
            
            for line in lines:
                line_lower = line.lower()
                
                # Skip until we find actual content (after scripture reference)
                if not found_content_start:
                    if scripture_match and scripture_match.group(1).lower() in line_lower:
                        found_content_start = True
                    continue
                
                # Stop at footer/donation content
                if any(pattern in line_lower for pattern in [
                    'mari memberkati', 'pancar pijar alkitab', 'bca 106.30066.22',
                    'yayasan lembaga sabda', 'webmaster@', '© '
                ]):
                    break
                
                # Skip header/navigation elements
                if any(skip in line_lower for skip in [
                    'sabda.org', 'publikasi', 'versi cetak', 'http://', 'https://',
                    'halaman ini adalah versi'
                ]):
                    continue
                
                # Keep substantial content lines
                if len(line) > 15:
                    text_lines.append(line)
            
            # Join text and split into logical paragraphs
            content_text = ' '.join(text_lines)
            
            # Split by common paragraph indicators
            potential_paragraphs = []
            
            # Method 1: Split by sentence patterns that indicate new paragraphs
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content_text)
            current_para = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                current_para.append(sentence)
                
                # Start new paragraph on certain patterns
                if (len(' '.join(current_para)) > 200 and 
                    (sentence.endswith('.') or sentence.endswith('!'))):
                    
                    para_text = ' '.join(current_para).strip()
                    if len(para_text) > 100:
                        potential_paragraphs.append(para_text)
                        current_para = []
            
            # Add remaining content
            if current_para:
                para_text = ' '.join(current_para).strip()
                if len(para_text) > 100:
                    potential_paragraphs.append(para_text)
            
            # If we still don't have good paragraphs, try splitting by logical breaks
            if len(potential_paragraphs) <= 1 and content_text:
                # Try splitting into 3 roughly equal parts
                words = content_text.split()
                if len(words) > 150:
                    third = len(words) // 3
                    para1 = ' '.join(words[:third])
                    para2 = ' '.join(words[third:2*third])
                    para3 = ' '.join(words[2*third:])
                    
                    paragraphs = [para1.strip(), para2.strip(), para3.strip()]
                else:
                    paragraphs = [content_text.strip()]
            else:
                paragraphs = potential_paragraphs
        
        # Clean up final paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            # Remove devotional title from beginning of first paragraph if present
            if devotional_title and para.startswith(devotional_title):
                para = para[len(devotional_title):].strip()
            
            # Remove author tags like [KRS]
            para = re.sub(r'\s*\[[\w\s]+\]\s*$', '', para).strip()
            
            if len(para) > 50:
                cleaned_paragraphs.append(para)
        
        # Structure the response
        content['devotional_content'] = cleaned_paragraphs
        content['full_text'] = clean_text
        content['word_count'] = len(clean_text.split())
        content['paragraph_count'] = len(cleaned_paragraphs)
        
        # Validate extracted content
        if not content['scripture_reference'] and not cleaned_paragraphs:
            logger.warning(f"Low quality content extracted from {url}")
        
        logger.info(f"Extracted {len(cleaned_paragraphs)} paragraphs from {url}")
        
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
        # Enhanced parameter validation
        validation_errors = []
        
        if not year:
            validation_errors.append("Year parameter is required (e.g., ?year=2025)")
        
        if not date:
            validation_errors.append("Date parameter is required in MMDD format (e.g., ?date=0902)")
        
        if validation_errors:
            return jsonify(create_response(
                status="error",
                message="; ".join(validation_errors),
                metadata={"error_type": "ValidationError"}
            )), 400
        
        # Validate year range
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 1:
            return jsonify(create_response(
                status="error",
                message=f"Year must be between 2000 and {current_year + 1}",
                metadata={"error_type": "ValidationError", "provided_year": year}
            )), 400
        
        # Enhanced date format validation
        if not re.match(r'^\d{4}$', date):
            return jsonify(create_response(
                status="error",
                message="Date must be in MMDD format (e.g., 0902 for September 2nd)",
                metadata={"error_type": "ValidationError", "provided_date": date}
            )), 400
        
        # Validate date range (month 01-12, day 01-31)
        try:
            month = int(date[:2])
            day = int(date[2:])
            if month < 1 or month > 12 or day < 1 or day > 31:
                raise ValueError("Invalid month or day")
        except ValueError:
            return jsonify(create_response(
                status="error",
                message="Invalid date. Month must be 01-12, day must be 01-31",
                metadata={"error_type": "ValidationError", "provided_date": date}
            )), 400
        
        # Scrape content
        result = scraper.scrape_sabda_content(year, date)
        
        # Add authentication and request info to metadata
        if result.get('metadata'):
            result['metadata'].update({
                'authenticated': True,
                'auth_method': 'JWT',
                'client_ip': get_client_ip(),
                'request_timestamp': datetime.now().isoformat()
            })
        
        status_code = 200 if result['status'] == 'success' else 500
        logger.info(f"Request completed with status: {result['status']}, code: {status_code}")
        return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Unexpected server error: {str(e)}")
        return jsonify(create_response(
            status="error",
            message="Internal server error occurred",
            metadata={
                "error_type": "ServerException",
                "client_ip": get_client_ip(),
                "timestamp": datetime.now().isoformat()
            }
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
        
        # Validate API key with rate limiting
        client_ip = get_client_ip()
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limit exceeded for token request from IP: {client_ip}")
            return jsonify(create_response(
                status="error",
                message="Too many token requests. Please try again later.",
                metadata={"error_type": "RateLimitError"}
            )), 429
        
        if api_key not in API_KEYS.values():
            logger.warning(f"Invalid API key attempt from IP: {client_ip}")
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
        logger.error(f"Token generation error: {str(e)}")
        return jsonify(create_response(
            status="error",
            message="Token generation failed",
            metadata={
                "error_type": "ServerException",
                "timestamp": datetime.now().isoformat()
            }
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
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SABDA Scraper API on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Cache TTL: {app.config['CACHE_TTL']} seconds")
    logger.info(f"Rate limit: {app.config['MAX_REQUESTS_PER_MINUTE']} requests/minute")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port, threaded=True)
