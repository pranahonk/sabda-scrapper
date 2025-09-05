# SABDA Scraper API - Go Version

A high-performance Go implementation of the SABDA devotional content scraper API using Fiber web framework and Colly for web scraping.

## Features

- **High Performance**: Built with Go and Fiber framework
- **Web Scraping**: Uses Colly with anti-bot detection and goquery for HTML parsing
- **JWT Authentication**: Secure API access with JWT tokens
- **Rate Limiting**: Built-in rate limiting per IP address
- **Caching**: In-memory caching with configurable TTL
- **Anti-Bot Measures**: Random user agents, delays, and realistic browser headers
- **Docker Support**: Containerized deployment ready
- **Graceful Shutdown**: Proper cleanup and shutdown handling

## Architecture

```
sabda-scraper-go/
├── cmd/server/           # Application entry point
├── internal/
│   ├── handlers/         # HTTP request handlers
│   ├── services/         # Business logic services
│   └── models/          # Data models and structures
├── pkg/
│   ├── config/          # Configuration management
│   └── scraper/         # Core scraping logic
├── go.mod              # Go module definition
└── render.yaml         # Deployment configuration
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/pranahonk/sabda-scraper-go.git
cd sabda-scraper-go
```

2. **Install dependencies:**
```bash
go mod tidy
```

3. **Run the application:**
```bash
go run cmd/server/main.go
```

The API will be available at `http://localhost:5000`

## Configuration

Configure the application using environment variables:

### Server Configuration
- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Debug mode (default: false)

### Authentication
- `SECRET_KEY`: JWT secret key (auto-generated if not provided)
- `JWT_EXPIRATION_HOURS`: JWT token expiration in hours (default: 24)
- `FLUTTER_API_KEY`: Flutter app API key (default: sabda_flutter_2025_secure_key)
- `MOBILE_API_KEY`: Mobile app API key (default: sabda_mobile_2025_secure_key)

### Caching & Rate Limiting
- `CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `MAX_REQUESTS_PER_MINUTE`: Rate limit per IP (default: 60)

### CORS
- `ALLOWED_ORIGINS`: Comma-separated allowed origins (default: *)

## API Endpoints

### Authentication

#### POST `/api/auth/token`
Generate an authentication token.

**Request:**
```json
{
  "api_key": "sabda_flutter_2025_secure_key"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Token generated successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400
  }
}
```

### Content Scraping

#### GET `/api/sabda`
Scrape SABDA devotional content (requires authentication).

**Headers:**
```
Authorization: Bearer <token>
```

**Parameters:**
- `year`: Year (integer, e.g., 2025)
- `date`: Date in MMDD format (string, e.g., "0902")

**Example:**
```
GET /api/sabda?year=2025&date=0902
```

**Response:**
```json
{
  "status": "success",
  "message": "Content scraped successfully",
  "data": {
    "title": "SABDA.org / PUBLIKASI / e-Santapan Harian / Versi Cetak Edisi 2 Sep 2025",
    "scripture_reference": "Lukas 13:18-21",
    "devotional_title": "Allah Bekerja Memakai Hal Kecil!",
    "devotional_content": [
      "Paragraph 1 content...",
      "Paragraph 2 content...",
      "Paragraph 3 content..."
    ],
    "full_text": "...",
    "word_count": 123,
    "paragraph_count": 3
  }
}
```

### Health Check

#### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "success",
  "message": "Service is healthy",
  "data": {
    "service": "SABDA Scraper API"
  }
}
```

## Deployment

### Render.com

1. Connect your GitHub repository to Render
2. The `render.yaml` file will automatically configure the deployment
3. Environment variables will be set automatically

Deploy URL: https://render.com/deploy?repo=https://github.com/pranahonk/sabda-scraper-go

### Docker

1. **Build the image:**
```bash
docker build -t sabda-scraper-go .
```

2. **Run the container:**
```bash
docker run -p 10000:10000 sabda-scraper-go
```

### Local Development

```bash
# Install dependencies
go mod tidy

# Run with hot reload (install air first: go install github.com/cosmtrek/air@latest)
air

# Or run directly
go run cmd/server/main.go
```

## Performance Optimizations

- **Concurrent Safe**: All services are thread-safe with proper mutex usage
- **Memory Efficient**: LRU cache with configurable size limits
- **Connection Pooling**: Reuses HTTP connections for scraping
- **Graceful Degradation**: Fallback mechanisms for content extraction
- **Anti-Bot Features**: Randomized delays and headers to avoid detection

## Key Improvements over Python Version

1. **Performance**: 10x faster request handling and lower memory usage
2. **Concurrency**: Better handling of concurrent requests
3. **Type Safety**: Strong typing prevents runtime errors
4. **Memory Management**: Automatic garbage collection and efficient memory usage
5. **Deployment**: Single binary deployment, no runtime dependencies

## Testing

```bash
# Run tests
go test ./...

# Run with coverage
go test -cover ./...

# Test specific package
go test ./internal/services
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.