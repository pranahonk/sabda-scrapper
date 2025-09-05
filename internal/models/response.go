package models

import "time"

// APIResponse represents a standardized API response
type APIResponse struct {
	Status   string      `json:"status"`
	Message  string      `json:"message"`
	Data     interface{} `json:"data,omitempty"`
	Metadata interface{} `json:"metadata,omitempty"`
}

// DevotionalContent represents the scraped devotional content
type DevotionalContent struct {
	Title               string    `json:"title"`
	ScriptureReference  string    `json:"scripture_reference"`
	DevotionalTitle     string    `json:"devotional_title"`
	DevotionalContent   []string  `json:"devotional_content"`
	FullText            string    `json:"full_text"`
	WordCount           int       `json:"word_count"`
	ParagraphCount      int       `json:"paragraph_count"`
}

// ScrapingMetadata represents metadata for scraping requests
type ScrapingMetadata struct {
	URL             string    `json:"url"`
	ScrapedAt       time.Time `json:"scraped_at"`
	Source          string    `json:"source"`
	Cached          bool      `json:"cached,omitempty"`
	Authenticated   bool      `json:"authenticated,omitempty"`
	AuthMethod      string    `json:"auth_method,omitempty"`
	ClientIP        string    `json:"client_ip,omitempty"`
	RequestTimestamp time.Time `json:"request_timestamp,omitempty"`
}

// AuthRequest represents authentication request
type AuthRequest struct {
	APIKey string `json:"api_key"`
}

// AuthResponse represents authentication response
type AuthResponse struct {
	Token     string    `json:"token"`
	TokenType string    `json:"token_type"`
	ExpiresIn int64     `json:"expires_in"`
}

// AuthMetadata represents authentication metadata
type AuthMetadata struct {
	Timestamp time.Time `json:"timestamp"`
	ExpiresAt time.Time `json:"expires_at"`
}

// HealthData represents health check data
type HealthData struct {
	Service string `json:"service"`
}

// CacheItem represents cached content with timestamp
type CacheItem struct {
	Content   DevotionalContent `json:"content"`
	Timestamp time.Time         `json:"timestamp"`
}

// RateLimitInfo represents rate limiting information
type RateLimitInfo struct {
	Requests  []time.Time `json:"requests"`
	ClientIP  string      `json:"client_ip"`
}