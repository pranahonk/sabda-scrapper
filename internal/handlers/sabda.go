package handlers

import (
	"log"
	"regexp"
	"strconv"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/pranahonk/sabda-scraper-go/internal/models"
	"github.com/pranahonk/sabda-scraper-go/internal/services"
)

// SABDAHandler handles SABDA scraping endpoints
type SABDAHandler struct {
	scraperService *services.ScraperService
}

// NewSABDAHandler creates a new SABDA handler
func NewSABDAHandler(scraperService *services.ScraperService) *SABDAHandler {
	return &SABDAHandler{
		scraperService: scraperService,
	}
}

// GetContent scrapes SABDA devotional content
func (h *SABDAHandler) GetContent(c *fiber.Ctx) error {
	// Get query parameters
	yearStr := c.Query("year")
	date := c.Query("date")

	// Enhanced parameter validation
	var validationErrors []string

	if yearStr == "" {
		validationErrors = append(validationErrors, "Year parameter is required (e.g., ?year=2025)")
	}

	if date == "" {
		validationErrors = append(validationErrors, "Date parameter is required in MMDD format (e.g., ?date=0902)")
	}

	if len(validationErrors) > 0 {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: joinStrings(validationErrors, "; "),
			Metadata: map[string]interface{}{
				"error_type": "ValidationError",
			},
		})
	}

	// Parse year
	year, err := strconv.Atoi(yearStr)
	if err != nil {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: "Year must be a valid integer",
			Metadata: map[string]interface{}{
				"error_type":    "ValidationError",
				"provided_year": yearStr,
			},
		})
	}

	// Validate year range
	currentYear := time.Now().Year()
	if year < 2000 || year > currentYear+1 {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: "Year must be between 2000 and " + strconv.Itoa(currentYear+1),
			Metadata: map[string]interface{}{
				"error_type":    "ValidationError",
				"provided_year": year,
			},
		})
	}

	// Enhanced date format validation
	dateRegex := regexp.MustCompile(`^\d{4}$`)
	if !dateRegex.MatchString(date) {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: "Date must be in MMDD format (e.g., 0902 for September 2nd)",
			Metadata: map[string]interface{}{
				"error_type":    "ValidationError",
				"provided_date": date,
			},
		})
	}

	// Validate date range (month 01-12, day 01-31)
	if len(date) == 4 {
		monthStr := date[:2]
		dayStr := date[2:]
		
		month, monthErr := strconv.Atoi(monthStr)
		day, dayErr := strconv.Atoi(dayStr)
		
		if monthErr != nil || dayErr != nil || month < 1 || month > 12 || day < 1 || day > 31 {
			return c.Status(400).JSON(models.APIResponse{
				Status:  "error",
				Message: "Invalid date. Month must be 01-12, day must be 01-31",
				Metadata: map[string]interface{}{
					"error_type":    "ValidationError",
					"provided_date": date,
				},
			})
		}
	}

	// Scrape content
	result, err := h.scraperService.ScrapeContent(year, date)
	if err != nil {
		log.Printf("Scraping error: %v", err)
		return c.Status(500).JSON(models.APIResponse{
			Status:  "error",
			Message: "Internal server error occurred",
			Metadata: map[string]interface{}{
				"error_type":        "ServerException",
				"client_ip":         c.Locals("client_ip"),
				"timestamp":         time.Now(),
			},
		})
	}

	// Add authentication and request info to metadata
	if metadata, ok := result.Metadata.(models.ScrapingMetadata); ok {
		metadata.Authenticated = true
		metadata.AuthMethod = "JWT"
		metadata.ClientIP = getClientIP(c)
		metadata.RequestTimestamp = time.Now()
		result.Metadata = metadata
	}

	statusCode := 200
	if result.Status != "success" {
		statusCode = 500
	}

	log.Printf("Request completed with status: %s, code: %d", result.Status, statusCode)
	return c.Status(statusCode).JSON(result)
}

// HealthCheck provides a health check endpoint
func (h *SABDAHandler) HealthCheck(c *fiber.Ctx) error {
	return c.JSON(models.APIResponse{
		Status:  "success",
		Message: "Service is healthy",
		Data: models.HealthData{
			Service: "SABDA Scraper API",
		},
		Metadata: map[string]interface{}{
			"timestamp": time.Now(),
		},
	})
}

// Home provides API documentation
func (h *SABDAHandler) Home(c *fiber.Ctx) error {
	return c.JSON(models.APIResponse{
		Status:  "success",
		Message: "API documentation retrieved successfully",
		Data: map[string]interface{}{
			"service": "SABDA Scraper API",
			"version": "2.0.0",
			"language": "Go",
			"endpoints": map[string]interface{}{
				"/api/auth/token": map[string]interface{}{
					"method":      "POST",
					"description": "Generate authentication token",
					"body": map[string]string{
						"api_key": "Your API key (string)",
					},
					"example": "POST with {\"api_key\": \"your_api_key\"}",
				},
				"/api/sabda": map[string]interface{}{
					"method":      "GET",
					"description": "Get SABDA devotional content (requires authentication)",
					"headers": map[string]string{
						"Authorization": "Bearer <token>",
					},
					"parameters": map[string]string{
						"year": "Year (integer, e.g., 2025)",
						"date": "Date in MMDD format (string, e.g., '0902' for September 2nd)",
					},
					"example": "/api/sabda?year=2025&date=0902",
				},
				"/api/health": map[string]interface{}{
					"method":      "GET",
					"description": "Health check endpoint",
				},
			},
			"authentication": map[string]interface{}{
				"type": "JWT Bearer Token",
				"flow": "1. POST /api/auth/token with api_key -> 2. Use returned token in Authorization header",
				"default_api_keys": map[string]string{
					"flutter_app": "sabda_flutter_2025_secure_key",
					"mobile_app":  "sabda_mobile_2025_secure_key",
				},
			},
		},
		Metadata: map[string]interface{}{
			"timestamp":     time.Now(),
			"cors_enabled":  true,
			"flutter_ready": true,
			"go_version":    true,
		},
	})
}

func joinStrings(strs []string, separator string) string {
	if len(strs) == 0 {
		return ""
	}
	if len(strs) == 1 {
		return strs[0]
	}
	
	result := strs[0]
	for i := 1; i < len(strs); i++ {
		result += separator + strs[i]
	}
	return result
}