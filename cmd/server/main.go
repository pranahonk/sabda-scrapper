package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"

	"github.com/pranahonk/sabda-scraper-go/internal/handlers"
	"github.com/pranahonk/sabda-scraper-go/internal/services"
	"github.com/pranahonk/sabda-scraper-go/pkg/config"
)

func main() {
	// Load configuration
	cfg := config.Load()

	log.Printf("Starting SABDA Scraper API on port %s", cfg.Server.Port)
	log.Printf("Debug mode: %v", cfg.Server.Debug)
	log.Printf("Cache TTL: %v", cfg.Cache.TTL)
	log.Printf("Rate limit: %d requests/minute", cfg.Rate.MaxRequestsPerMinute)

	// Initialize services
	cacheService := services.NewCacheService(cfg.Cache.TTL, cfg.Cache.MaxSize)
	rateLimitService := services.NewRateLimitService(cfg.Rate.MaxRequestsPerMinute, cfg.Rate.WindowDuration)
	authService := services.NewAuthService(
		cfg.JWT.SecretKey,
		cfg.JWT.ExpirationDelta,
		map[string]string{
			"flutter": cfg.API.FlutterKey,
			"mobile":  cfg.API.MobileKey,
		},
	)
	scraperService := services.NewScraperService(cfg.Server.Debug, cacheService)

	// Initialize handlers
	authHandler := handlers.NewAuthHandler(authService, rateLimitService)
	sabdaHandler := handlers.NewSABDAHandler(scraperService)

	// Create Fiber app
	app := fiber.New(fiber.Config{
		ReadTimeout:    cfg.Server.Timeout,
		WriteTimeout:   cfg.Server.Timeout,
		IdleTimeout:    cfg.Server.IdleTimeout,
		StrictRouting:  true,
		CaseSensitive:  true,
		ServerHeader:   "SABDA-Scraper-Go",
		AppName:        "SABDA Scraper API v2.0",
		ErrorHandler:   customErrorHandler,
	})

	// Middleware
	app.Use(recover.New())
	
	if cfg.Server.Debug {
		app.Use(logger.New(logger.Config{
			Format: "${time} ${method} ${path} ${status} ${latency}\n",
		}))
	}

	// CORS middleware
	app.Use(cors.New(cors.Config{
		AllowOrigins: joinStrings(cfg.CORS.AllowedOrigins, ","),
		AllowMethods: joinStrings(cfg.CORS.AllowedMethods, ","),
		AllowHeaders: joinStrings(cfg.CORS.AllowedHeaders, ","),
	}))

	// Routes
	setupRoutes(app, authHandler, sabdaHandler)

	// Graceful shutdown
	go func() {
		if err := app.Listen(cfg.Server.Host + ":" + cfg.Server.Port); err != nil {
			log.Printf("Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	log.Println("Shutting down server...")
	
	// Graceful shutdown with timeout
	if err := app.ShutdownWithTimeout(30 * time.Second); err != nil {
		log.Printf("Server shutdown error: %v", err)
	}

	log.Println("Server stopped")
}

func setupRoutes(app *fiber.App, authHandler *handlers.AuthHandler, sabdaHandler *handlers.SABDAHandler) {
	// API routes
	api := app.Group("/api")

	// Public routes (must be defined before protected routes)
	api.Get("/health", sabdaHandler.HealthCheck)
	api.Post("/auth/token", authHandler.GetToken)

	// Protected routes
	api.Get("/sabda", authHandler.AuthMiddleware(), sabdaHandler.GetContent)

	// Home route (public)
	app.Get("/", sabdaHandler.Home)
}

func customErrorHandler(c *fiber.Ctx, err error) error {
	code := fiber.StatusInternalServerError

	if e, ok := err.(*fiber.Error); ok {
		code = e.Code
	}

	return c.Status(code).JSON(fiber.Map{
		"status":  "error",
		"message": err.Error(),
		"metadata": map[string]interface{}{
			"error_type": "ServerError",
			"timestamp":  time.Now(),
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