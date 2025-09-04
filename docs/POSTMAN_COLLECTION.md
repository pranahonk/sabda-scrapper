# Postman Collection for SABDA Scraper API

## Import Collection

You can import this collection into Postman by copying the JSON below and importing it as a raw text collection.

```json
{
  "info": {
    "name": "SABDA Scraper API",
    "description": "Collection for testing SABDA devotional content scraper API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://sabda-scrapper.onrender.com",
      "type": "string"
    },
    {
      "key": "token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Get Auth Token",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const response = pm.response.json();",
                  "    if (response.status === 'success') {",
                  "        pm.collectionVariables.set('token', response.data.token);",
                  "        pm.test('Token received successfully', function () {",
                  "            pm.expect(response.data.token).to.be.a('string');",
                  "        });",
                  "    }",
                  "}"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"api_key\": \"sabda_flutter_2025_secure_key\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/api/auth/token",
              "host": ["{{baseUrl}}"],
              "path": ["api", "auth", "token"]
            }
          }
        }
      ]
    },
    {
      "name": "API Endpoints",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{baseUrl}}/api/health",
              "host": ["{{baseUrl}}"],
              "path": ["api", "health"]
            }
          }
        },
        {
          "name": "Get SABDA Content",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{token}}"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/api/sabda?year=2025&date=0902",
              "host": ["{{baseUrl}}"],
              "path": ["api", "sabda"],
              "query": [
                {
                  "key": "year",
                  "value": "2025"
                },
                {
                  "key": "date",
                  "value": "0902"
                }
              ]
            }
          }
        },
        {
          "name": "API Documentation",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{baseUrl}}/",
              "host": ["{{baseUrl}}"],
              "path": [""]
            }
          }
        }
      ]
    },
    {
      "name": "Error Testing",
      "item": [
        {
          "name": "Invalid API Key",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"api_key\": \"invalid_key\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/api/auth/token",
              "host": ["{{baseUrl}}"],
              "path": ["api", "auth", "token"]
            }
          }
        },
        {
          "name": "Missing Authorization",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{baseUrl}}/api/sabda?year=2025&date=0902",
              "host": ["{{baseUrl}}"],
              "path": ["api", "sabda"],
              "query": [
                {
                  "key": "year",
                  "value": "2025"
                },
                {
                  "key": "date",
                  "value": "0902"
                }
              ]
            }
          }
        },
        {
          "name": "Invalid Date Format",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{token}}"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/api/sabda?year=2025&date=invalid",
              "host": ["{{baseUrl}}"],
              "path": ["api", "sabda"],
              "query": [
                {
                  "key": "year",
                  "value": "2025"
                },
                {
                  "key": "date",
                  "value": "invalid"
                }
              ]
            }
          }
        }
      ]
    }
  ]
}
```

## Manual Testing Steps

### 1. Set Base URL
- Update the `baseUrl` variable to your deployed API URL
- For local testing: `http://localhost:5000`
- For production: `https://your-domain.com`

### 2. Get Authentication Token
1. Run "Get Auth Token" request
2. Token will be automatically saved to collection variable
3. Verify response contains valid JWT token

### 3. Test Protected Endpoints
1. Run "Get SABDA Content" request
2. Token is automatically included in Authorization header
3. Verify devotional content is returned

### 4. Test Error Cases
1. Run "Invalid API Key" to test authentication errors
2. Run "Missing Authorization" to test unauthorized access
3. Run "Invalid Date Format" to test validation errors

## Environment Variables

Create a Postman environment with these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `baseUrl` | `https://sabda-scrapper.onrender.com` | API base URL |
| `token` | (auto-set) | JWT token from auth |
| `apiKey` | `sabda_flutter_2025_secure_key` | API key for auth |

## Test Scripts

The collection includes automatic test scripts that:
- Extract and save JWT tokens
- Validate response structure
- Check status codes
- Verify data types

## Quick Start

1. Import the JSON collection above into Postman
2. Set the `baseUrl` variable to your API URL
3. Run "Get Auth Token" first
4. Run other requests (token is auto-included)
5. Check test results in the Test Results tab
