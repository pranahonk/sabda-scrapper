package scraper

import (
	"fmt"
	"log"
	"math/rand"
	"regexp"
	"strings"
	"time"
	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
	"github.com/pranahonk/sabda-scraper-go/internal/models"
)

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// SABDAScraper handles scraping SABDA devotional content
type SABDAScraper struct {
	collector *colly.Collector
}

// New creates a new SABDA scraper instance
func New(debug bool) *SABDAScraper {
	c := colly.NewCollector(
		colly.UserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
	)

	// Debug logging is handled by the collector's built-in logging

	// Set random delays between requests (1-3 seconds)
	c.Limit(&colly.LimitRule{
		DomainGlob:  "*",
		Parallelism: 1,
		Delay:       1 * time.Second,
	})

	// Set timeouts
	c.SetRequestTimeout(30 * time.Second)

	// Random user agents
	userAgents := []string{
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
	}

	// Set anti-bot headers
	c.OnRequest(func(r *colly.Request) {
		// Random user agent
		r.Headers.Set("User-Agent", userAgents[rand.Intn(len(userAgents))])
		
		// Anti-bot headers
		r.Headers.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
		r.Headers.Set("Accept-Language", "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7")
		r.Headers.Set("Accept-Encoding", "gzip, deflate, br")
		r.Headers.Set("DNT", "1")
		r.Headers.Set("Connection", "keep-alive")
		r.Headers.Set("Upgrade-Insecure-Requests", "1")
		r.Headers.Set("Sec-Fetch-Dest", "document")
		r.Headers.Set("Sec-Fetch-Mode", "navigate")
		r.Headers.Set("Sec-Fetch-Site", "none")
		r.Headers.Set("Cache-Control", "max-age=0")

		// Add random delay before request
		delay := time.Duration(rand.Intn(2000)+1000) * time.Millisecond
		time.Sleep(delay)
	})

	// Error handling
	c.OnError(func(r *colly.Response, err error) {
		log.Printf("Error scraping %s: %v", r.Request.URL, err)
	})

	return &SABDAScraper{
		collector: c,
	}
}

// ScrapeContent scrapes devotional content from SABDA website
func (s *SABDAScraper) ScrapeContent(year int, date string) (*models.DevotionalContent, error) {
	// Format date to MMDD
	formattedDate := fmt.Sprintf("%04s", date)
	if len(formattedDate) != 4 {
		return nil, fmt.Errorf("date must be in MMDD format")
	}

	// Try the direct content URL first, fallback to print view if needed
	url := fmt.Sprintf("https://www.sabda.org/publikasi/e-sh/%d/%s/%s", year, formattedDate[:2], formattedDate[2:])
	printURL := fmt.Sprintf("https://www.sabda.org/publikasi/e-sh/cetak/?tahun=%d&edisi=%s", year, formattedDate)
	log.Printf("Scraping URL: %s", url)

	var content models.DevotionalContent
	var scrapingError error

	s.collector.OnHTML("html", func(e *colly.HTMLElement) {
		// Extract title
		title := e.ChildText("title")
		if title == "" {
			title = "SABDA Devotional"
		}
		content.Title = strings.TrimSpace(title)

		
		var mainContent *goquery.Selection
		
		// Look for the main devotional content in aside.w elements
		if sel := e.DOM.Find("aside.w"); sel.Length() > 0 {
			// Find the aside that contains paragraphs (devotional content)
			sel.Each(func(i int, aside *goquery.Selection) {
				if aside.Find("P").Length() > 0 {
					mainContent = aside
					return
				}
			})
		}
		
		// Fallback to previous logic if aside.w not found
		if mainContent == nil {
			if sel := e.DOM.Find("td.wj"); sel.Length() > 0 {
				mainContent = sel.First()
			} else if sel := e.DOM.Find("table td"); sel.Length() > 0 {
				
				var largestCell *goquery.Selection
				maxLength := 0
				sel.Each(func(i int, cell *goquery.Selection) {
					text := strings.TrimSpace(cell.Text())
					if len(text) > maxLength {
						maxLength = len(text)
						largestCell = cell
					}
				})
				if largestCell != nil {
					mainContent = largestCell
				}
			} else {
				mainContent = e.DOM.Find("body").First()
			}
		}

		// Extract all text for processing
		allText := mainContent.Text()
		log.Printf("Raw text length: %d", len(allText))
		if len(allText) > 0 {
			log.Printf("First 500 chars: %s", allText[:min(500, len(allText))])
		}
		
		// Also try to extract HTML content for better parsing
		htmlContent, _ := mainContent.Html()
		log.Printf("HTML content length: %d", len(htmlContent))
		
		lines := strings.Split(allText, "\n")
		var cleanLines []string
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" && !s.isHeaderContent(strings.ToLower(line)) {
				cleanLines = append(cleanLines, line)
			}
		}
		cleanText := strings.Join(cleanLines, "\n")
		log.Printf("Clean text length: %d", len(cleanText))
		
		// If we have very little content, the page might not have loaded properly
		if len(cleanText) < 100 {
			log.Printf("Warning: Very little content extracted, page might not have loaded properly")
		}

		// Extract scripture reference - first try from h1 or title elements
		scriptureRef := ""
		if h1 := e.DOM.Find("h1"); h1.Length() > 0 {
			h1Text := h1.Text()
			// Look for scripture reference in h1 (e.g., "Mazmur 1")
			scriptureRegex := regexp.MustCompile(`\b([A-Za-z]+\s+\d+(?::\d+(?:-\d+)?)?)\b`)
			if match := scriptureRegex.FindStringSubmatch(h1Text); len(match) > 1 {
				scriptureRef = match[1]
			}
		}
		
		// Fallback to searching in the main text
		if scriptureRef == "" {
			scriptureRegex := regexp.MustCompile(`\b([A-Za-z]+\s+\d+:\d+(?:-\d+)?)\b`)
			if match := scriptureRegex.FindStringSubmatch(cleanText); len(match) > 1 {
				scriptureRef = match[1]
			}
		}
		
		// Update scripture reference after potential extraction from h1
		content.ScriptureReference = scriptureRef

		// Extract devotional title - first try from h1 element
		devotionalTitle := ""
		if h1 := e.DOM.Find("h1"); h1.Length() > 0 {
			h1Text := strings.TrimSpace(h1.Text())
			
			// Extract scripture reference from title if not found yet
			if scriptureRef == "" {
				scriptureRegex := regexp.MustCompile(`^([A-Za-z]+\s+\d+(?::\d+(?:-\d+)?)?)(.*)`)
				if match := scriptureRegex.FindStringSubmatch(h1Text); len(match) > 2 {
					scriptureRef = strings.TrimSpace(match[1])
					devotionalTitle = strings.TrimSpace(match[2])
				}
			} else {
				// Remove scripture reference from title if present
				h1Text = strings.ReplaceAll(h1Text, scriptureRef, "")
				devotionalTitle = strings.TrimSpace(h1Text)
			}
			
			// Clean up the title
			if devotionalTitle != "" && len(devotionalTitle) > 3 {
				// Keep the cleaned title
			} else if h1Text != "" && len(h1Text) > 3 {
				devotionalTitle = h1Text
			}
		}
		
		// Fallback to text-based extraction
		if devotionalTitle == "" {
			devotionalTitle = s.extractDevotionalTitle(cleanText, scriptureRef)
		}
		content.DevotionalTitle = devotionalTitle
		
		// Update scripture reference after all extractions
		content.ScriptureReference = scriptureRef

		
		content.DevotionalContent = s.extractParagraphs(mainContent)

		
		if len(content.DevotionalContent) == 0 {
			content.DevotionalContent = s.extractParagraphsFromText(cleanText)
		}

		
		content.FullText = s.buildFullText(content.DevotionalContent)
		content.WordCount = len(strings.Fields(content.FullText))
		content.ParagraphCount = len(content.DevotionalContent)

		log.Printf("Extracted %d paragraphs from %s", content.ParagraphCount, url)
	})

	// Visit the URL - try direct URL first, then fallback to print URL
	err := s.collector.Visit(url)
	if err != nil || len(content.DevotionalContent) == 0 {
		log.Printf("Direct URL failed or no content, trying print URL: %s", printURL)
		if err := s.collector.Visit(printURL); err != nil {
			return nil, fmt.Errorf("failed to scrape both URLs %s and %s: %w", url, printURL, err)
		}
	}

	if scrapingError != nil {
		return nil, scrapingError
	}

	
	if content.ScriptureReference == "" && len(content.DevotionalContent) == 0 {
		log.Printf("Warning: Low quality content extracted from %s", url)
	}

	return &content, nil
}

func (s *SABDAScraper) extractDevotionalTitle(text, scriptureRef string) string {
	lines := strings.Split(text, "\n")
	
	// Look for patterns that indicate a title
	titlePatterns := []string{
		"Critical Thinking",
		"Berpikir Kritis",
	}
	
	// First try to find known title patterns
	for _, line := range lines {
		line = strings.TrimSpace(line)
		for _, pattern := range titlePatterns {
			if strings.Contains(line, pattern) {
				return pattern
			}
		}
	}
	
	// If scripture reference exists, look for title after it
	if scriptureRef != "" {
		for i, line := range lines {
			if strings.Contains(line, scriptureRef) && i+1 < len(lines) {
				nextLine := strings.TrimSpace(lines[i+1])
				if len(nextLine) > 3 && len(nextLine) < 50 && 
				   !strings.HasPrefix(strings.ToLower(nextLine), "ketika") &&
				   !strings.Contains(strings.ToLower(nextLine), "diperhadapkan") {
					// Clean up the title
					title := regexp.MustCompile(`\[.*?\]|\s{2,}`).ReplaceAllString(nextLine, " ")
					title = strings.TrimSpace(title)
					if title != "" {
						return title
					}
				}
			}
		}
	}
	
	// Fallback: look for short lines that could be titles
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if len(line) > 5 && len(line) < 30 && 
		   !strings.Contains(strings.ToLower(line), "sabda") &&
		   !strings.Contains(strings.ToLower(line), "publikasi") &&
		   !regexp.MustCompile(`\d+:\d+`).MatchString(line) {
			return line
		}
	}
	
	return ""
}

func (s *SABDAScraper) extractParagraphs(selection *goquery.Selection) []string {
	var paragraphs []string

	// Look for both lowercase and uppercase P tags
	selection.Find("p, P").Each(func(i int, p *goquery.Selection) {
		text := strings.TrimSpace(p.Text())
		
		
		if text == "" || text == "\u00a0" {
			return
		}

		
		if align, exists := p.Attr("align"); exists && align == "center" {
			return
		}

		
		if s.isDonationContent(text) {
			return
		}

		
		if len(text) < 50 {
			return
		}

		
		text = regexp.MustCompile(`\s{2,}`).ReplaceAllString(text, " ")
		paragraphs = append(paragraphs, text)
	})

	
	if len(paragraphs) <= 1 {
		log.Println("Using text-based paragraph extraction")
		paragraphs = s.extractParagraphsFromText(selection.Text())
	}

	
	var cleanedParagraphs []string
	for _, para := range paragraphs {
		
		para = regexp.MustCompile(`\s*\[[\w\s]+\]\s*$`).ReplaceAllString(para, "")
		para = strings.TrimSpace(para)

		if len(para) > 50 {
			cleanedParagraphs = append(cleanedParagraphs, para)
		}
	}

	return cleanedParagraphs
}

func (s *SABDAScraper) extractParagraphsFromText(text string) []string {
	var paragraphs []string
	
	lines := strings.Split(text, "\n")
	var textLines []string
	foundContentStart := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		lineLower := strings.ToLower(line)

		
		if !foundContentStart {
			if strings.Contains(lineLower, "lukas") || strings.Contains(lineLower, "matius") || 
			   strings.Contains(lineLower, "markus") || strings.Contains(lineLower, "yohanes") {
				foundContentStart = true
			}
			continue
		}

		
		if s.isDonationContent(line) {
			break
		}

		
		if s.isHeaderContent(lineLower) {
			continue
		}

		
		if len(line) > 15 {
			textLines = append(textLines, line)
		}
	}

	
	contentText := strings.Join(textLines, " ")

	if len(contentText) > 300 {
		
		sentences := regexp.MustCompile(`(?:[.!?])\s+(?=[A-Z])`).Split(contentText, -1)
		var currentPara []string

		for _, sentence := range sentences {
			sentence = strings.TrimSpace(sentence)
			if sentence == "" {
				continue
			}

			currentPara = append(currentPara, sentence)

			
			if len(strings.Join(currentPara, " ")) > 200 {
				paraText := strings.Join(currentPara, " ")
				if len(paraText) > 100 {
					paragraphs = append(paragraphs, paraText)
					currentPara = []string{}
				}
			}
		}

		
		if len(currentPara) > 0 {
			paraText := strings.Join(currentPara, " ")
			if len(paraText) > 100 {
				paragraphs = append(paragraphs, paraText)
			}
		}
	}

	
	if len(paragraphs) <= 1 && len(contentText) > 0 {
		words := strings.Fields(contentText)
		if len(words) > 150 {
			third := len(words) / 3
			para1 := strings.Join(words[:third], " ")
			para2 := strings.Join(words[third:2*third], " ")
			para3 := strings.Join(words[2*third:], " ")
			
			paragraphs = []string{
				strings.TrimSpace(para1),
				strings.TrimSpace(para2),
				strings.TrimSpace(para3),
			}
		} else if contentText != "" {
			paragraphs = []string{strings.TrimSpace(contentText)}
		}
	}

	return paragraphs
}

// buildFullText creates the full text from devotional content
func (s *SABDAScraper) buildFullText(paragraphs []string) string {
	if len(paragraphs) == 0 {
		return ""
	}
	
	// Use the last paragraph as the full text summary (usually contains the main message)
	if len(paragraphs) > 0 {
		return paragraphs[len(paragraphs)-1]
	}
	
	return strings.Join(paragraphs, " ")
}

func (s *SABDAScraper) isDonationContent(text string) bool {
	textLower := strings.ToLower(text)
	donationPatterns := []string{
		"mari memberkati",
		"pancar pijar alkitab",
		"bca 106.30066.22",
		"yayasan lembaga sabda",
		"webmaster@",
		"ylsa.org",
		"copyright",
		"© ",
		"santapan harian",
	}

	for _, pattern := range donationPatterns {
		if strings.Contains(textLower, pattern) {
			return true
		}
	}
	return false
}

func (s *SABDAScraper) isHeaderContent(text string) bool {
	headerPatterns := []string{
		"sabda.org",
		"publikasi",
		"versi cetak",
		"http://",
		"https://",
		"halaman ini adalah versi",
	}

	for _, pattern := range headerPatterns {
		if strings.Contains(text, pattern) {
			return true
		}
	}
	return false
}