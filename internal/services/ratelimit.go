package services

import (
	"sync"
	"time"

	"github.com/pranahonk/sabda-scraper-go/internal/models"
)

// RateLimitService handles rate limiting
type RateLimitService struct {
	clients    map[string]*models.RateLimitInfo
	mutex      sync.RWMutex
	maxReqs    int
	window     time.Duration
}

// NewRateLimitService creates a new rate limiting service
func NewRateLimitService(maxRequestsPerMinute int, windowDuration time.Duration) *RateLimitService {
	service := &RateLimitService{
		clients: make(map[string]*models.RateLimitInfo),
		maxReqs: maxRequestsPerMinute,
		window:  windowDuration,
	}

	// Start cleanup goroutine
	go service.cleanup()

	return service
}

// IsAllowed checks if a request from the given IP is allowed
func (r *RateLimitService) IsAllowed(clientIP string) bool {
	r.mutex.Lock()
	defer r.mutex.Unlock()

	now := time.Now()
	
	// Get or create client info
	client, exists := r.clients[clientIP]
	if !exists {
		client = &models.RateLimitInfo{
			ClientIP:  clientIP,
			Requests:  make([]time.Time, 0),
		}
		r.clients[clientIP] = client
	}

	// Clean old requests outside the window
	var validRequests []time.Time
	for _, reqTime := range client.Requests {
		if now.Sub(reqTime) < r.window {
			validRequests = append(validRequests, reqTime)
		}
	}
	client.Requests = validRequests

	// Check if limit exceeded
	if len(client.Requests) >= r.maxReqs {
		return false
	}

	// Add current request
	client.Requests = append(client.Requests, now)
	return true
}

// GetRequestCount returns the current request count for a client
func (r *RateLimitService) GetRequestCount(clientIP string) int {
	r.mutex.RLock()
	defer r.mutex.RUnlock()

	client, exists := r.clients[clientIP]
	if !exists {
		return 0
	}

	now := time.Now()
	count := 0
	for _, reqTime := range client.Requests {
		if now.Sub(reqTime) < r.window {
			count++
		}
	}
	
	return count
}

// Reset clears all rate limit data for a client
func (r *RateLimitService) Reset(clientIP string) {
	r.mutex.Lock()
	defer r.mutex.Unlock()

	delete(r.clients, clientIP)
}

// Clear removes all rate limit data
func (r *RateLimitService) Clear() {
	r.mutex.Lock()
	defer r.mutex.Unlock()

	r.clients = make(map[string]*models.RateLimitInfo)
}

func (r *RateLimitService) cleanup() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			r.mutex.Lock()
			now := time.Now()
			
			for clientIP, client := range r.clients {
				// Clean old requests
				var validRequests []time.Time
				for _, reqTime := range client.Requests {
					if now.Sub(reqTime) < r.window {
						validRequests = append(validRequests, reqTime)
					}
				}
				
				if len(validRequests) == 0 {
					// Remove client if no recent requests
					delete(r.clients, clientIP)
				} else {
					client.Requests = validRequests
				}
			}
			
			r.mutex.Unlock()
		}
	}
}