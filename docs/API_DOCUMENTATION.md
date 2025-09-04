# SABDA Scraper API Documentation

## Overview

The SABDA Scraper API provides secure access to daily devotional content from SABDA.org. It features JWT-based authentication, CORS support for web applications, and standardized JSON responses.

## Base URL

```
Production: https://sabda-scrapper.onrender.com
Development: http://localhost:5000
```

## Authentication

The API uses JWT (JSON Web Token) authentication. You must first obtain a token using your API key, then include it in subsequent requests.

### API Keys

Contact the administrator to obtain an API key. Available keys:
- `sabda_flutter_2025_secure_key` - For Flutter mobile apps
- `sabda_mobile_2025_secure_key` - For other mobile applications

## Endpoints

### 1. Authentication

#### POST `/api/auth/token`

Obtain a JWT token for API access.

**Request:**
```json
{
  "api_key": "your_api_key_here"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Token generated successfully",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer"
  },
  "metadata": {
    "expires_at": "2025-01-03T10:30:00Z",
    "issued_at": "2025-01-02T10:30:00Z",
    "api_key_hash": "sha256_hash"
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Invalid API key",
  "data": null,
  "metadata": {
    "error_type": "AuthenticationError"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing API key
- `401` - Invalid API key
- `500` - Server error

### 2. Get SABDA Content

#### GET `/api/sabda`

Retrieve devotional content for a specific date.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `year` (required): Year (2000-2026)
- `date` (required): Date in MMDD format (e.g., "0902" for September 2nd)

**Example Request:**
```
GET /api/sabda?year=2025&date=0902
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Content retrieved successfully",
  "data": {
    "title": "SABDA Devotional - September 2, 2025",
    "scripture_reference": "John 3:16",
    "devotional_title": "God's Love",
    "devotional_content": [
      "For God so loved the world that he gave his one and only Son...",
      "This verse reminds us of the depth of God's love...",
      "We are called to respond to this love..."
    ],
    "full_text": "Complete devotional text...",
    "word_count": 245
  },
  "metadata": {
    "url": "https://www.sabda.org/publikasi/e-sh/cetak/?tahun=2025&edisi=0902",
    "source": "https://www.sabda.org/publikasi/e-sh/2025/09/02/",
    "scraped_at": "2025-01-02T10:30:00Z",
    "copyright": "Copyright © 1997- now Yayasan Lembaga SABDA (YLSA).",
    "provider": "SABDA.org",
    "year": 2025,
    "date": "0902",
    "authenticated": true,
    "auth_method": "JWT"
  }
}
```

**Response (Error - Missing Parameters):**
```json
{
  "status": "error",
  "message": "Year parameter is required (e.g., ?year=2025)",
  "data": null,
  "metadata": {
    "error_type": "ValidationError"
  }
}
```

**Response (Error - Invalid Date Format):**
```json
{
  "status": "error",
  "message": "Date must be in MMDD format (e.g., 0902 for September 2nd)",
  "data": null,
  "metadata": {
    "error_type": "ValidationError"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid parameters
- `401` - Unauthorized (missing/invalid token)
- `500` - Server error (scraping failed)

### 3. Health Check

#### GET `/api/health`

Check API health status.

**Response:**
```json
{
  "status": "success",
  "message": "API is healthy",
  "data": {
    "service": "SABDA Scraper API",
    "version": "1.0.0",
    "uptime": "2 hours, 15 minutes"
  },
  "metadata": {
    "timestamp": "2025-01-02T10:30:00Z",
    "environment": "production"
  }
}
```

**Status Codes:**
- `200` - API is healthy

### 4. API Documentation

#### GET `/`

Get API documentation and available endpoints.

**Response:**
```json
{
  "status": "success",
  "message": "SABDA Scraper API Documentation",
  "data": {
    "service": "SABDA Scraper API",
    "version": "1.0.0",
    "description": "API for scraping devotional content from SABDA.org",
    "endpoints": [
      {
        "path": "/api/auth/token",
        "method": "POST",
        "description": "Get JWT authentication token",
        "authentication": false
      },
      {
        "path": "/api/sabda",
        "method": "GET",
        "description": "Get devotional content",
        "authentication": true,
        "parameters": ["year", "date"]
      },
      {
        "path": "/api/health",
        "method": "GET",
        "description": "Health check endpoint",
        "authentication": false
      }
    ]
  },
  "metadata": {
    "documentation": "https://sabda-scrapper.onrender.com/docs",
    "support": "sabda-api@support.com"
  }
}
```

## Response Format

All API responses follow a standardized format:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": "Response data or null",
  "metadata": {
    "additional_info": "value"
  }
}
```

### Status Values
- `success` - Request completed successfully
- `error` - Request failed

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "status": "error",
  "message": "Authorization header missing",
  "data": null,
  "metadata": {
    "error_type": "AuthenticationError"
  }
}
```

**403 Forbidden:**
```json
{
  "status": "error",
  "message": "Invalid or expired token",
  "data": null,
  "metadata": {
    "error_type": "TokenError"
  }
}
```

**500 Server Error:**
```json
{
  "status": "error",
  "message": "Failed to scrape content from SABDA.org",
  "data": null,
  "metadata": {
    "error_type": "ScrapingError",
    "source_url": "https://sabda.org/devotion/2025/09/02"
  }
}
```

## Rate Limiting

- **Authentication endpoint:** 10 requests per minute per IP
- **Content endpoint:** 60 requests per hour per token
- **Health check:** No limits

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) for web applications:

- **Allowed Origins:** All (`*`)
- **Allowed Methods:** GET, POST, OPTIONS
- **Allowed Headers:** Content-Type, Authorization
- **Credentials:** Supported

## Security

### JWT Tokens
- **Algorithm:** HS256
- **Expiration:** 24 hours
- **Claims:** API key hash, issued at, expires at

### Best Practices
1. Store JWT tokens securely
2. Refresh tokens before expiration
3. Use HTTPS in production
4. Don't expose API keys in client-side code
5. Implement proper error handling

## SDK Examples

### cURL
```bash
# Get token
curl -X POST https://sabda-scrapper.onrender.com/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_api_key"}'

# Get content
curl -X GET "https://sabda-scrapper.onrender.com/api/sabda?year=2025&date=0902" \
  -H "Authorization: Bearer your_jwt_token"
```

### JavaScript (Fetch)
```javascript
// Get token
const tokenResponse = await fetch('/api/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ api_key: 'your_api_key' })
});
const tokenData = await tokenResponse.json();

// Get content
const contentResponse = await fetch('/api/sabda?year=2025&date=0902', {
  headers: { 'Authorization': `Bearer ${tokenData.data.token}` }
});
const contentData = await contentResponse.json();
```

### Python (requests)
```python
import requests

# Get token
token_response = requests.post('/api/auth/token', 
  json={'api_key': 'your_api_key'})
token = token_response.json()['data']['token']

# Get content
content_response = requests.get('/api/sabda?year=2025&date=0902',
  headers={'Authorization': f'Bearer {token}'})
content = content_response.json()
```

## Deployment

The API can be deployed on various platforms:

- **Render** (Recommended)
- **Railway**
- **Heroku**
- **Docker**

See deployment configuration files in the repository.

## Support

For API support, issues, or feature requests:
- **GitHub:** https://github.com/your-repo
- **Email:** your-email@domain.com
- **Documentation:** https://your-domain.com/docs

## Changelog

### v1.0.0 (2025-01-02)
- Initial release
- JWT authentication
- SABDA content scraping
- CORS support
- Standardized JSON responses
- Health check endpoint
