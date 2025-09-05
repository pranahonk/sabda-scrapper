package services

import (
	"sync"
	"time"

	"github.com/pranahonk/sabda-scraper-go/internal/models"
)

// CacheService handles content caching
type CacheService struct {
	cache   map[string]models.CacheItem
	mutex   sync.RWMutex
	ttl     time.Duration
	maxSize int
}

// NewCacheService creates a new cache service
func NewCacheService(ttl time.Duration, maxSize int) *CacheService {
	service := &CacheService{
		cache:   make(map[string]models.CacheItem),
		ttl:     ttl,
		maxSize: maxSize,
	}

	// Start cleanup goroutine
	go service.cleanupExpired()

	return service
}

// Get retrieves content from cache
func (c *CacheService) Get(key string) (*models.DevotionalContent, bool) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	item, exists := c.cache[key]
	if !exists {
		return nil, false
	}

	// Check if expired
	if time.Since(item.Timestamp) > c.ttl {
		return nil, false
	}

	return &item.Content, true
}

// Set stores content in cache
func (c *CacheService) Set(key string, content models.DevotionalContent) {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	// Remove oldest entries if cache is full
	if len(c.cache) >= c.maxSize {
		c.removeOldest()
	}

	c.cache[key] = models.CacheItem{
		Content:   content,
		Timestamp: time.Now(),
	}
}

// Clear removes all items from cache
func (c *CacheService) Clear() {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.cache = make(map[string]models.CacheItem)
}

// Size returns the current cache size
func (c *CacheService) Size() int {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	return len(c.cache)
}

func (c *CacheService) removeOldest() {
	var oldestKey string
	var oldestTime time.Time

	for key, item := range c.cache {
		if oldestKey == "" || item.Timestamp.Before(oldestTime) {
			oldestKey = key
			oldestTime = item.Timestamp
		}
	}

	if oldestKey != "" {
		delete(c.cache, oldestKey)
	}
}

func (c *CacheService) cleanupExpired() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.mutex.Lock()
			now := time.Now()
			for key, item := range c.cache {
				if now.Sub(item.Timestamp) > c.ttl {
					delete(c.cache, key)
				}
			}
			c.mutex.Unlock()
		}
	}
}