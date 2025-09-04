# SABDA Scraper API Documentation

## Overview

The SABDA Scraper API provides access to daily devotional content from SABDA.org with JWT-based authentication and CORS support for Flutter applications.

**Base URL:**
```
Production: https://sabda-scrapper.onrender.com
Development: http://localhost:5000
```
**Version:** 2.0.0  
**Authentication:** JWT Bearer Token

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Flutter Integration](#flutter-integration)
- [Rate Limiting](#rate-limiting)

## Authentication

The API uses JWT (JSON Web Token) authentication. All protected endpoints require a valid Bearer token.

### API Keys

Default API keys for development:
- **Flutter App:** `sabda_flutter_2025_secure_key`
- **Mobile App:** `sabda_mobile_2025_secure_key`

### Authentication Flow

1. **Get Token:** POST `/api/auth/token` with API key
2. **Use Token:** Include `Authorization: Bearer <token>` header in requests
3. **Token Expiry:** Tokens expire after 24 hours

## Endpoints

### 1. Generate Authentication Token

**Endpoint:** `POST /api/auth/token`

**Description:** Generate a JWT token for API access

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "sabda_flutter_2025_secure_key"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Token generated successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400
  },
  "metadata": {
    "timestamp": "2025-09-03T22:06:36.193111",
    "expires_at": "2025-09-04T15:06:36.193116"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "status": "error",
  "message": "Invalid API key",
  "metadata": {
    "error_type": "AuthenticationError"
  }
}
```

### 2. Get SABDA Devotional Content

**Endpoint:** `GET /api/sabda`

**Description:** Retrieve devotional content for a specific date

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `year` (required): Year as integer (e.g., 2025)
- `date` (required): Date in MMDD format (e.g., "0902" for September 2nd)

**Example Request:**
```
GET /api/sabda?year=2025&date=0902
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Content scraped successfully",
  "data": {
    "title": "SABDA.org / PUBLIKASI / e-Santapan Harian / Versi Cetak Edisi 2 Sep 2025",
    "scripture_reference": "Lukas 13:18-21",
    "devotional_title": "Allah Bekerja Memakai Hal Kecil!",
    "devotional_content": [
      "Hal kecil sering dipandang sebelah mata, tidak dianggap dan dikesampingkan..."
    ],
    "full_text": "Complete text content...",
    "word_count": 361
  },
  "metadata": {
    "url": "https://www.sabda.org/publikasi/e-sh/cetak/?tahun=2025&edisi=0902",
    "scraped_at": "2025-09-03T22:05:10.806385",
    "source": "SABDA.org",
    "authenticated": true,
    "auth_method": "JWT"
  }
}
```

### 3. Health Check

**Endpoint:** `GET /api/health`

**Description:** Check API service health

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Service is healthy",
  "data": {
    "service": "SABDA Scraper API"
  },
  "metadata": {
    "timestamp": "2025-09-03T22:06:22.764629"
  }
}
```

### 4. API Documentation

**Endpoint:** `GET /`

**Description:** Get API documentation and endpoint information

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "API documentation retrieved successfully",
  "data": {
    "service": "SABDA Scraper API",
    "version": "2.0.0",
    "endpoints": { ... },
    "authentication": { ... }
  },
  "metadata": {
    "timestamp": "2025-09-03T22:06:36.193111",
    "cors_enabled": true,
    "flutter_ready": true,
    "architecture": "modular"
  }
}
```

## Response Format

All API responses follow a standardized format:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": { /* Response data (optional) */ },
  "metadata": { /* Additional information (optional) */ }
}
```

### Status Codes

- **200 OK:** Request successful
- **400 Bad Request:** Invalid request parameters
- **401 Unauthorized:** Authentication required or invalid token
- **500 Internal Server Error:** Server error

## Error Handling

### Common Error Responses

**Missing Authentication:**
```json
{
  "status": "error",
  "message": "Authorization header is required",
  "metadata": {
    "error_type": "AuthenticationError"
  }
}
```

**Invalid Token:**
```json
{
  "status": "error",
  "message": "Invalid or expired token",
  "metadata": {
    "error_type": "AuthenticationError"
  }
}
```

**Invalid Parameters:**
```json
{
  "status": "error",
  "message": "Year parameter is required (e.g., ?year=2025)"
}
```

**Server Error:**
```json
{
  "status": "error",
  "message": "Server error: Connection timeout",
  "metadata": {
    "error_type": "ServerException"
  }
}
```

## Flutter Integration

### Installation

Add to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
```

### Usage Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class SabdaApiService {
  static const String baseUrl = 'https://your-api-domain.com';
  static const String apiKey = 'sabda_flutter_2025_secure_key';
  
  String? _token;
  DateTime? _tokenExpiry;

  // Authenticate and get token
  Future<bool> authenticate() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'api_key': apiKey}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['status'] == 'success') {
        _token = data['data']['token'];
        _tokenExpiry = DateTime.parse(data['metadata']['expires_at']);
        return true;
      }
    }
    return false;
  }

  // Get devotional content
  Future<Map<String, dynamic>?> getSabdaContent(int year, String date) async {
    if (!isAuthenticated) {
      await authenticate();
    }

    final response = await http.get(
      Uri.parse('$baseUrl/api/sabda?year=$year&date=$date'),
      headers: {
        'Authorization': 'Bearer $_token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['data'];
    }
    return null;
  }

  bool get isAuthenticated => 
    _token != null && 
    _tokenExpiry != null && 
    DateTime.now().isBefore(_tokenExpiry!);
}
```

### Error Handling in Flutter

```dart
try {
  final data = await apiService.getSabdaContent(2025, '0902');
  if (data != null) {
    // Use the data
    print('Title: ${data['devotional_title']}');
  }
} catch (e) {
  // Handle errors
  print('Error: $e');
}
```

## Rate Limiting

- **Authentication:** No specific limit
- **Content Requests:** Built-in delays (2-5 seconds) to respect source website
- **Recommendation:** Cache responses to minimize requests

## Date Format Guide

The `date` parameter uses MMDD format:

| Date | Format | Example |
|------|--------|---------|
| January 1st | 0101 | `?date=0101` |
| February 14th | 0214 | `?date=0214` |
| September 2nd | 0902 | `?date=0902` |
| December 25th | 1225 | `?date=1225` |

## Security Notes

1. **API Keys:** Store securely, never commit to version control
2. **Tokens:** Automatically expire after 24 hours
3. **HTTPS:** Always use HTTPS in production
4. **CORS:** Enabled for web applications

## Support

For issues or questions:
- Check the health endpoint: `GET /api/health`
- Review error messages in the response
- Ensure proper authentication headers

## Changelog

### Version 2.0.0
- Modular architecture
- JWT authentication
- CORS support
- Standardized responses
- Flutter integration examples
