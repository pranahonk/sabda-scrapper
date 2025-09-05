package models

import "time"

// Config represents application configuration
type Config struct {
	Server ServerConfig `mapstructure:"server"`
	JWT    JWTConfig    `mapstructure:"jwt"`
	Cache  CacheConfig  `mapstructure:"cache"`
	Rate   RateConfig   `mapstructure:"rate"`
	API    APIConfig    `mapstructure:"api"`
	CORS   CORSConfig   `mapstructure:"cors"`
}

// ServerConfig represents server configuration
type ServerConfig struct {
	Port        string        `mapstructure:"port"`
	Host        string        `mapstructure:"host"`
	Debug       bool          `mapstructure:"debug"`
	Timeout     time.Duration `mapstructure:"timeout"`
	IdleTimeout time.Duration `mapstructure:"idle_timeout"`
}

// JWTConfig represents JWT configuration
type JWTConfig struct {
	SecretKey        string        `mapstructure:"secret_key"`
	ExpirationHours  int           `mapstructure:"expiration_hours"`
	ExpirationDelta  time.Duration `mapstructure:"-"`
}

// CacheConfig represents cache configuration
type CacheConfig struct {
	TTLSeconds int           `mapstructure:"ttl_seconds"`
	TTL        time.Duration `mapstructure:"-"`
	MaxSize    int           `mapstructure:"max_size"`
}

// RateConfig represents rate limiting configuration
type RateConfig struct {
	MaxRequestsPerMinute int           `mapstructure:"max_requests_per_minute"`
	WindowDuration       time.Duration `mapstructure:"-"`
	CleanupInterval      time.Duration `mapstructure:"-"`
}

// APIConfig represents API keys configuration
type APIConfig struct {
	FlutterKey string `mapstructure:"flutter_key"`
	MobileKey  string `mapstructure:"mobile_key"`
}

// CORSConfig represents CORS configuration
type CORSConfig struct {
	AllowedOrigins []string `mapstructure:"allowed_origins"`
	AllowedMethods []string `mapstructure:"allowed_methods"`
	AllowedHeaders []string `mapstructure:"allowed_headers"`
}