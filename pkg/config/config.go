package config

import (
	"crypto/rand"
	"encoding/hex"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/pranahonk/sabda-scraper-go/internal/models"
	"github.com/spf13/viper"
)

// Load loads configuration from environment variables and config files
func Load() *models.Config {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("./config")
	
	// Set defaults
	setDefaults()
	
	// Read from environment variables
	viper.AutomaticEnv()
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	
	// Try to read config file (optional)
	if err := viper.ReadInConfig(); err != nil {
		log.Printf("Config file not found, using environment variables and defaults: %v", err)
	}
	
	var config models.Config
	if err := viper.Unmarshal(&config); err != nil {
		log.Fatalf("Unable to decode config: %v", err)
	}
	
	// Set computed fields
	config.JWT.ExpirationDelta = time.Duration(config.JWT.ExpirationHours) * time.Hour
	config.Cache.TTL = time.Duration(config.Cache.TTLSeconds) * time.Second
	config.Rate.WindowDuration = time.Minute
	config.Rate.CleanupInterval = 5 * time.Minute
	
	// Generate secret key if not provided
	if config.JWT.SecretKey == "" {
		config.JWT.SecretKey = generateSecretKey()
	}
	
	return &config
}

func setDefaults() {
	// Server defaults
	viper.SetDefault("server.port", getEnvOrDefault("PORT", "5000"))
	viper.SetDefault("server.host", "0.0.0.0")
	viper.SetDefault("server.debug", getEnvBoolOrDefault("GO_DEBUG", false))
	viper.SetDefault("server.timeout", 30*time.Second)
	viper.SetDefault("server.idle_timeout", 120*time.Second)
	
	// JWT defaults
	viper.SetDefault("jwt.secret_key", os.Getenv("SECRET_KEY"))
	viper.SetDefault("jwt.expiration_hours", getEnvIntOrDefault("JWT_EXPIRATION_HOURS", 24))
	
	// Cache defaults
	viper.SetDefault("cache.ttl_seconds", getEnvIntOrDefault("CACHE_TTL", 3600))
	viper.SetDefault("cache.max_size", getEnvIntOrDefault("CACHE_MAX_SIZE", 1000))
	
	// Rate limiting defaults
	viper.SetDefault("rate.max_requests_per_minute", getEnvIntOrDefault("MAX_REQUESTS_PER_MINUTE", 60))
	
	// API keys defaults
	viper.SetDefault("api.flutter_key", getEnvOrDefault("FLUTTER_API_KEY", "sabda_flutter_2025_secure_key"))
	viper.SetDefault("api.mobile_key", getEnvOrDefault("MOBILE_API_KEY", "sabda_mobile_2025_secure_key"))
	
	// CORS defaults
	allowedOrigins := strings.Split(getEnvOrDefault("ALLOWED_ORIGINS", "*"), ",")
	viper.SetDefault("cors.allowed_origins", allowedOrigins)
	viper.SetDefault("cors.allowed_methods", []string{"GET", "POST", "OPTIONS"})
	viper.SetDefault("cors.allowed_headers", []string{"Content-Type", "Authorization"})
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvIntOrDefault(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvBoolOrDefault(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if value == "true" || value == "1" {
			return true
		}
		if value == "false" || value == "0" {
			return false
		}
	}
	return defaultValue
}

func generateSecretKey() string {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		log.Fatalf("Failed to generate secret key: %v", err)
	}
	return hex.EncodeToString(bytes)
}