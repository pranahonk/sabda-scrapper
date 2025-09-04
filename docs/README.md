# SABDA Scraper API Documentation

## Quick Links

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with endpoints, authentication, and examples
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment instructions for various platforms
- **[Flutter Integration](FLUTTER_INTEGRATION.md)** - Complete Flutter SDK with examples and best practices
- **[Postman Collection](POSTMAN_COLLECTION.md)** - Ready-to-use Postman collection for API testing

## Overview

The SABDA Scraper API provides secure access to daily devotional content from SABDA.org with JWT authentication, CORS support, and standardized JSON responses.

## Features

- 🔐 **JWT Authentication** - Secure token-based authentication
- 🌐 **CORS Enabled** - Ready for web and mobile app integration
- 📱 **Flutter Ready** - Complete Flutter SDK included
- 🛡️ **Anti-Bot Protection** - Bypasses Cloudflare protection
- 📊 **Standardized Responses** - Consistent JSON response format
- 🚀 **Multiple Deployment Options** - Render, Railway, Heroku, Docker
- 📚 **Comprehensive Documentation** - API docs, examples, and guides
- ✅ **Production Ready** - Security best practices and error handling

## Quick Start

### 1. Get Authentication Token

```bash
curl -X POST https://sabda-scrapper.onrender.com/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sabda_flutter_2025_secure_key"}'
```

### 2. Fetch Devotional Content

```bash
curl -X GET "https://sabda-scrapper.onrender.com/api/sabda?year=2025&date=0902" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/token` | POST | No | Get JWT authentication token |
| `/api/sabda` | GET | Yes | Get devotional content for specific date |
| `/api/health` | GET | No | Health check endpoint |
| `/` | GET | No | API documentation |

## Response Format

All responses follow a standardized format:

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

## Authentication

1. **Obtain API Key** - Contact administrator for API key
2. **Get JWT Token** - Exchange API key for JWT token
3. **Use Token** - Include token in Authorization header for protected endpoints

Available API keys:
- `sabda_flutter_2025_secure_key` - For Flutter mobile apps
- `sabda_mobile_2025_secure_key` - For other mobile applications

## Flutter Integration

Complete Flutter SDK with automatic token management:

```dart
final apiService = SabdaApiService();
await apiService.init();

// Get today's content
final content = await apiService.getTodaysContent();

// Get specific date content
final content = await apiService.getSabdaContent(2025, "0902");
```

See [Flutter Integration Guide](FLUTTER_INTEGRATION.md) for complete implementation.

## Deployment

### Recommended: Render

1. Connect your GitHub repository to Render
2. Set environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=your_super_secret_key_here_min_32_chars
   FLUTTER_API_KEY=sabda_flutter_2025_secure_key
   MOBILE_API_KEY=sabda_mobile_2025_secure_key
   ```
3. Deploy automatically from Git

See [Deployment Guide](DEPLOYMENT_GUIDE.md) for all platform options.

## Testing

### Postman Collection

Import the provided Postman collection for comprehensive API testing:
- Authentication flow
- Content retrieval
- Error handling
- Automatic token management

See [Postman Collection](POSTMAN_COLLECTION.md) for setup instructions.

### Manual Testing

```bash
# Health check
curl https://sabda-scrapper.onrender.com/api/health

# Get token
TOKEN=$(curl -s -X POST https://sabda-scrapper.onrender.com/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sabda_flutter_2025_secure_key"}' | \
  jq -r '.data.token')

# Get content
curl -H "Authorization: Bearer $TOKEN" \
  "https://sabda-scrapper.onrender.com/api/sabda?year=2025&date=0902"
```

## Security Features

- **JWT Token Authentication** with 24-hour expiration
- **API Key Validation** with SHA-256 hashing
- **CORS Configuration** for cross-origin requests
- **Rate Limiting** (recommended for production)
- **HTTPS Support** (automatic on most platforms)
- **Error Handling** without sensitive information exposure

## Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/your-repo/sabda-scraper.git
cd sabda-scraper

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run development server
python run.py
```

### Project Structure

```
sabda-scraper/
├── app/
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── utils/           # Utilities
│   └── config.py        # Configuration
├── docs/                # Documentation
├── tests/               # Unit tests
├── requirements.txt     # Dependencies
├── run.py              # Application entry point
└── deployment files    # Platform configs
```

## Error Handling

The API provides detailed error responses:

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

Common error types:
- `AuthenticationError` - Invalid API key or token
- `ValidationError` - Invalid request parameters
- `ScrapingError` - Failed to retrieve content
- `ServerError` - Internal server error

## Rate Limits

- **Authentication:** 10 requests/minute per IP
- **Content API:** 60 requests/hour per token
- **Health Check:** No limits

## Support

- **Documentation:** Complete guides in `/docs` folder
- **GitHub Issues:** Report bugs and feature requests
- **API Status:** Monitor `/api/health` endpoint

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v1.0.0 (2025-01-02)
- Initial release
- JWT authentication system
- SABDA content scraping
- CORS support for web/mobile apps
- Comprehensive documentation
- Multiple deployment options
- Flutter SDK integration
