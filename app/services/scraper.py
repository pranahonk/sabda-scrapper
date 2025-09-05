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
            
            formatted_date = date.zfill(4)
            
            
            url = f"https://www.sabda.org/publikasi/e-sh/cetak/?tahun={year}&edisi={formatted_date}"
            
            
            source_url = f"https://www.sabda.org/publikasi/e-sh/{year}/{formatted_date[:2]}/{formatted_date[2:]}/"
            
            
            delay_min = current_app.config.get('SCRAPING_DELAY_MIN', 2)
            delay_max = current_app.config.get('SCRAPING_DELAY_MAX', 5)
            time.sleep(random.uniform(delay_min, delay_max))
            
            
            timeout = current_app.config.get('SCRAPING_TIMEOUT', 15)
            response = self.scraper.get(url, headers=self.get_random_headers(), timeout=timeout)
            response.raise_for_status()
            
            
            soup = BeautifulSoup(response.content, 'html5lib')
            
            
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
        
        
        title_tag = soup.find('title')
        content['title'] = title_tag.text.strip() if title_tag else None
        
        
        main_text = soup.get_text()
        
        
        lines = [line.strip() for line in main_text.split('\n') if line.strip()]
        
        
        filtered_lines = []
        for line in lines:
            if ('Mari memberkati para hamba Tuhan' in line or 
                'melalui edisi Santapan Harian' in line or
                'BCA 106.30066.22 Yay Pancar Pijar Alkitab' in line or
                'Kirim dukungan Anda ke:' in line):
                continue
            filtered_lines.append(line)
        
        clean_text = '\n'.join(filtered_lines)
        
        scripture_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)', clean_text)
        content['scripture_reference'] = scripture_match.group(1) if scripture_match else None
        
        title_match = re.search(r'([A-Za-z]+\s+\d+:\d+(?:-\d+)?)(.+?)(?=\n|$)', clean_text)
        if title_match:
            devotional_title = title_match.group(2).strip()
            devotional_title = re.sub(r'\[.*?\]', '', devotional_title).strip()
            content['devotional_title'] = devotional_title
            
        
        
        html_content = str(soup)
        html_content = re.sub(r'<p[^>]*>\s*<small>.*?Mari memberkati.*?Yay Pancar Pijar Alkitab.*?</small>\s*</p>', '', html_content, flags=re.DOTALL)
        
        
        cleaned_soup = BeautifulSoup(html_content, 'html5lib')
        
        
        paragraph_tags = cleaned_soup.find_all('p')
        paragraphs = []
        
        for p_tag in paragraph_tags:
            
            text = p_tag.get_text().strip()
            if not text or text == '&nbsp;' or len(text) < 20:
                continue
                
            
            if any(skip in text.lower() for skip in ['sabda.org', 'publikasi', 'versi cetak', 'http://', 'https://']):
                continue
                
            
            if any(footer in text.lower() for footer in ['yayasan lembaga sabda', 'webmaster@', 'ylsa.org']):
                continue
                
            
            if any(donation in text.lower() for donation in ['mari memberkati', 'bca 106.30066.22', 'yay pancar pijar']):
                continue
                
            
            clean_text = re.sub(r'\s+', ' ', text).strip()
            
            if clean_text and len(clean_text) > 20:
                paragraphs.append(clean_text)
        
        final_paragraphs = []
        for paragraph in paragraphs:
            
            cleaned_paragraph = re.sub(r'\[PMS\].*', '', paragraph, flags=re.DOTALL)
            cleaned_paragraph = re.sub(r'Mari memberkati.*', '', cleaned_paragraph, flags=re.DOTALL)
            cleaned_paragraph = re.sub(r'.*BCA 106\.30066\.22.*', '', cleaned_paragraph, flags=re.DOTALL)
            cleaned_paragraph = re.sub(r'Kirim dukungan.*', '', cleaned_paragraph, flags=re.DOTALL)
            
            
            cleaned_paragraph = re.sub(r'\s+', ' ', cleaned_paragraph).strip()
            
            
            if cleaned_paragraph and len(cleaned_paragraph) > 30:
                final_paragraphs.append(cleaned_paragraph)
        
        content['devotional_content'] = final_paragraphs
        content['full_text'] = clean_text
        content['word_count'] = len(clean_text.split())
        
        return content
