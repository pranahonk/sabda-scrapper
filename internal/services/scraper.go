package services

import (
	"fmt"
	"log"
	"time"

	"github.com/pranahonk/sabda-scraper-go/internal/models"
	"github.com/pranahonk/sabda-scraper-go/pkg/scraper"
)

// ScraperService handles scraping operations with caching
type ScraperService struct {
	scraper *scraper.SABDAScraper
	cache   *CacheService
}

// NewScraperService creates a new scraper service
func NewScraperService(debug bool, cache *CacheService) *ScraperService {
	return &ScraperService{
		scraper: scraper.New(debug),
		cache:   cache,
	}
}

// ScrapeContent scrapes devotional content with caching
func (s *ScraperService) ScrapeContent(year int, date string) (*models.APIResponse, error) {
	// Create cache key
	formattedDate := fmt.Sprintf("%04s", date)
	cacheKey := fmt.Sprintf("sabda_%d_%s", year, formattedDate)

	// Check cache first
	if cached, found := s.cache.Get(cacheKey); found {
		log.Printf("Cache hit for key: %s", cacheKey)
		
		return &models.APIResponse{
			Status:  "success",
			Message: "Content retrieved from cache",
			Data:    cached,
			Metadata: models.ScrapingMetadata{
				URL:       fmt.Sprintf("https://www.sabda.org/publikasi/e-sh/cetak/?tahun=%d&edisi=%s", year, formattedDate),
				Source:    "SABDA.org",
				Cached:    true,
				ScrapedAt: time.Now(),
			},
		}, nil
	}

	// Scrape content
	content, err := s.scraper.ScrapeContent(year, date)
	if err != nil {
		return &models.APIResponse{
			Status:  "error",
			Message: fmt.Sprintf("Scraping failed: %v", err),
			Metadata: map[string]interface{}{
				"url":        fmt.Sprintf("https://www.sabda.org/publikasi/e-sh/cetak/?tahun=%d&edisi=%s", year, formattedDate),
				"error_type": "ScrapingException",
			},
		}, err
	}

	// Cache the result
	s.cache.Set(cacheKey, *content)

	return &models.APIResponse{
		Status:  "success",
		Message: "Content scraped successfully",
		Data:    content,
		Metadata: models.ScrapingMetadata{
			URL:       fmt.Sprintf("https://www.sabda.org/publikasi/e-sh/cetak/?tahun=%d&edisi=%s", year, formattedDate),
			Source:    "SABDA.org",
			Cached:    false,
			ScrapedAt: time.Now(),
		},
	}, nil
}