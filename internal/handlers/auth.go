package handlers

import (
	"log"
	"strings"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/pranahonk/sabda-scraper-go/internal/models"
	"github.com/pranahonk/sabda-scraper-go/internal/services"
)

// AuthHandler handles authentication-related endpoints
type AuthHandler struct {
	authService     *services.AuthService
	rateLimitService *services.RateLimitService
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(authService *services.AuthService, rateLimitService *services.RateLimitService) *AuthHandler {
	return &AuthHandler{
		authService:     authService,
		rateLimitService: rateLimitService,
	}
}

// GetToken generates an authentication token
func (h *AuthHandler) GetToken(c *fiber.Ctx) error {
	clientIP := getClientIP(c)

	// Check rate limit
	if !h.rateLimitService.IsAllowed(clientIP) {
		log.Printf("Rate limit exceeded for token request from IP: %s", clientIP)
		return c.Status(429).JSON(models.APIResponse{
			Status:  "error",
			Message: "Too many token requests. Please try again later.",
			Metadata: map[string]interface{}{
				"error_type": "RateLimitError",
			},
		})
	}

	var req models.AuthRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: "Invalid request body",
			Metadata: map[string]interface{}{
				"error_type": "ValidationError",
			},
		})
	}

	if req.APIKey == "" {
		return c.Status(400).JSON(models.APIResponse{
			Status:  "error",
			Message: "API key is required in request body",
			Metadata: map[string]interface{}{
				"error_type": "AuthenticationError",
			},
		})
	}

	// Generate token
	token, expiresAt, err := h.authService.GenerateToken(req.APIKey)
	if err != nil {
		log.Printf("Invalid API key attempt from IP: %s", clientIP)
		return c.Status(401).JSON(models.APIResponse{
			Status:  "error",
			Message: "Invalid API key",
			Metadata: map[string]interface{}{
				"error_type": "AuthenticationError",
			},
		})
	}

	return c.JSON(models.APIResponse{
		Status:  "success",
		Message: "Token generated successfully",
		Data: models.AuthResponse{
			Token:     token,
			TokenType: "Bearer",
			ExpiresIn: int64(time.Until(expiresAt).Seconds()),
		},
		Metadata: models.AuthMetadata{
			Timestamp: time.Now(),
			ExpiresAt: expiresAt,
		},
	})
}

// AuthMiddleware validates JWT tokens
func (h *AuthHandler) AuthMiddleware() fiber.Handler {
	return func(c *fiber.Ctx) error {
		clientIP := getClientIP(c)

		// Check rate limit
		if !h.rateLimitService.IsAllowed(clientIP) {
			log.Printf("Rate limit exceeded for IP: %s", clientIP)
			return c.Status(429).JSON(models.APIResponse{
				Status:  "error",
				Message: "Rate limit exceeded. Please try again later.",
				Metadata: map[string]interface{}{
					"error_type": "RateLimitError",
				},
			})
		}

		authHeader := c.Get("Authorization")
		if authHeader == "" {
			log.Printf("Missing auth header from IP: %s", clientIP)
			return c.Status(401).JSON(models.APIResponse{
				Status:  "error",
				Message: "Authorization header is required",
				Metadata: map[string]interface{}{
					"error_type": "AuthenticationError",
				},
			})
		}

		// Extract token from "Bearer <token>" format
		var token string
		if strings.HasPrefix(authHeader, "Bearer ") {
			token = strings.TrimPrefix(authHeader, "Bearer ")
		} else {
			token = authHeader
		}

		if token == "" {
			log.Printf("Invalid auth header format from IP: %s", clientIP)
			return c.Status(401).JSON(models.APIResponse{
				Status:  "error",
				Message: "Invalid authorization header format. Use 'Bearer <token>'",
				Metadata: map[string]interface{}{
					"error_type": "AuthenticationError",
				},
			})
		}

		// Verify token
		claims, err := h.authService.VerifyToken(token)
		if err != nil {
			log.Printf("Token verification failed from IP: %s, error: %v", clientIP, err)
			return c.Status(401).JSON(models.APIResponse{
				Status:  "error",
				Message: "Invalid or expired token",
				Metadata: map[string]interface{}{
					"error_type": "AuthenticationError",
				},
			})
		}

		// Store claims in context
		c.Locals("claims", claims)
		c.Locals("client_ip", clientIP)

		return c.Next()
	}
}

func getClientIP(c *fiber.Ctx) string {
	// Check X-Forwarded-For header first (for proxies)
	if xff := c.Get("X-Forwarded-For"); xff != "" {
		ips := strings.Split(xff, ",")
		return strings.TrimSpace(ips[0])
	}
	
	// Check X-Real-IP header
	if xri := c.Get("X-Real-IP"); xri != "" {
		return xri
	}
	
	// Fall back to remote IP
	return c.IP()
}