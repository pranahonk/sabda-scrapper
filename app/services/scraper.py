import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import random
from fake_useragent import UserAgent
import cloudscraper
from flask import current_app
from app.utils.response import create_response

class SABDAScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.ua = UserAgent()
        
    def get_random_headers(self):
        """Generate random headers to avoid bot detection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def scrape_sabda_content(self, year, date):
        """Scrape content from SABDA website with anti-bot measures"""
        try:
            # Format the date parameter (MMDD format)
            formatted_date = date.zfill(4)
            
            # Construct URL
            url = f"https://www.sabda.org/publikasi/e-sh/cetak/?tahun={year}&edisi={formatted_date}"
            
            # Construct source URL for metadata
            source_url = f"https://www.sabda.org/publikasi/e-sh/{year}/{formatted_date[:2]}/{formatted_date[2:]}/"
            
            # Add random delay to avoid being detected as bot
            delay_min = current_app.config.get('SCRAPING_DELAY_MIN', 2)
            delay_max = current_app.config.get('SCRAPING_DELAY_MAX', 5)
            time.sleep(random.uniform(delay_min, delay_max))
            
            # Make request with cloudscraper (bypasses Cloudflare)
            timeout = current_app.config.get('SCRAPING_TIMEOUT', 15)
            response = self.scraper.get(url, headers=self.get_random_headers(), timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # Extract content
            content_data = self.extract_content(soup, url)
            
            return create_response(
                status="success",
                message="Content scraped successfully",
                data=content_data,
                metadata={
                    "url": url,
                    "source": source_url,
                    "scraped_at": datetime.now().isoformat(),
                    "copyright": f"Copyright © 1997-{datetime.now().year} Yayasan Lembaga SABDA (YLSA).",
                    "provider": "SABDA.org"
                }
            )
            
        except requests.exceptions.RequestException as e:
            return create_response(
                status="error",
                message=f"Request failed: {str(e)}",
                metadata={
                    "url": url if 'url' in locals() else None,
                    "error_type": "RequestException"
                }
            )
        except Exception as e:
            return create_response(
                status="error",
                message=f"Scraping failed: {str(e)}",
                metadata={
                    "url": url if 'url' in locals() else None,
                    "error_type": "GeneralException"
                }
            )
    
    def extract_content(self, soup, url):
        """Extract and structure content from the parsed HTML"""
        content = {}
        
        # Extract title
        title_tag = soup.find('title')
        content['title'] = title_tag.text.strip() if title_tag else None
        
        # Get all text content
        main_text = soup.get_text()
        
        # Clean up the text and remove donation footer
        lines = [line.strip() for line in main_text.split('\n') if line.strip()]
        
        # Filter out donation footer text
        filtered_lines = []
        for line in lines:
            # Skip the donation footer text
            if ('Mari memberkati para hamba Tuhan' in line or 
                'melalui edisi Santapan Harian' in line or
                'BCA 106.30066.22 Yay Pancar Pijar Alkitab' in line or
                'Kirim dukungan Anda ke:' in line):
                continue
            filtered_lines.append(line)
        
        clean_text = '\n'.join(filtered_lines)
        
        # Extract scripture reference (pattern like "Lukas 13:18-21")
        scripture_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)', clean_text)
        content['scripture_reference'] = scripture_match.group(1) if scripture_match else None
        
        # Extract devotional title (usually after scripture reference)
        title_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)(.+?)(?=\n|$)', clean_text)
        if title_match:
            devotional_title = title_match.group(2).strip()
            # Remove any links or extra formatting
            devotional_title = re.sub(r'\[.*?\]', '', devotional_title).strip()
            content['devotional_title'] = devotional_title
        
        # Extract main devotional content (paragraphs between scripture and footer)
        paragraphs = []
        current_paragraph = []
        
        for line in lines:
            # Skip header/navigation elements
            if any(skip in line.lower() for skip in ['sabda.org', 'publikasi', 'versi cetak', 'http://', 'https://']):
                continue
            
            # Skip footer elements
            if any(footer in line.lower() for footer in ['yayasan lembaga sabda', 'webmaster@', 'ylsa.org']):
                break
                
            # If line looks like a paragraph content
            if len(line) > 20 and not line.startswith('[') and not line.endswith(']'):
                current_paragraph.append(line)
            elif current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # Add last paragraph if exists
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        content['devotional_content'] = paragraphs
        content['full_text'] = clean_text
        content['word_count'] = len(clean_text.split())
        
        return content
