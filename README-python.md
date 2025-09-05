# SABDA Scraper API

A Python Flask API to scrape devotional content from SABDA.org and convert it to JSON format.

## Features

- Web scraping with anti-bot detection using cloudscraper
- Random user agents and headers to avoid detection
- Flask REST API with query parameters
- JSON output for easy integration
- Error handling and validation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### GET /api/sabda
Scrape SABDA devotional content for a specific date.

**Parameters:**
- `year` (integer): Year (e.g., 2025)
- `date` (string): Date in MMDD format (e.g., "0902" for September 2nd)

**Example:**
```
GET http://localhost:5000/api/sabda?year=2025&date=0902
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "SABDA.org / PUBLIKASI / e-Santapan Harian / Versi Cetak Edisi 2 Sep 2025",
    "scripture_reference": "Lukas 13:18-21",
    "devotional_title": "Allah Bekerja Memakai Hal Kecil!",
    "devotional_content": ["paragraph1", "paragraph2", ...],
    "full_text": "...",
    "word_count": 123
  },
  "url": "https://www.sabda.org/publikasi/e-sh/cetak/?tahun=2025&edisi=0902",
  "scraped_at": "2025-09-02T21:56:00.000000"
}
```

### GET /api/health
Health check endpoint.

### GET /
API documentation and service information.

## Testing with Postman

1. Start the Flask application
2. In Postman, create a GET request to:
   ```
   http://localhost:5000/api/sabda?year=2025&date=0902
   ```
3. Send the request to get the JSON response

## Anti-Bot Features

- Uses cloudscraper to bypass Cloudflare protection
- Random user agents via fake-useragent
- Random delays between requests
- Realistic browser headers
- Session management for cookie persistence
# sabda-scrapper
