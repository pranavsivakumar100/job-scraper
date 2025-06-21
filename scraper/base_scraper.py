from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import logging

try:
    from playwright.sync_api import sync_playwright  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobData:
    title: str
    company: str
    location: str
    url: str
    remote_type: Optional[str] = None
    department: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    posted_date: Optional[datetime] = None

class BaseScraper(ABC):
    """Base class for all company career page scrapers"""
    
    def __init__(self, company_name: str, base_url: str, use_playwright: bool = False):
        self.company_name = company_name
        self.base_url = base_url
        self.use_playwright = use_playwright
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def get_page_content(self, url: str) -> str:
        """Get page content using either requests or playwright"""
        if self.use_playwright:
            return self._get_content_playwright(url)
        else:
            return self._get_content_requests(url)
    
    def _get_content_requests(self, url: str) -> str:
        """Get page content using requests"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    def _get_content_playwright(self, url: str) -> str:
        """Get page content using playwright (for JS-heavy pages)"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available. Install it with: pip install playwright")
            return ""
            
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url)
                page.wait_for_load_state("networkidle")
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logger.error(f"Error fetching {url} with playwright: {e}")
            return ""
    
    def parse_salary(self, salary_text: str) -> tuple[Optional[float], Optional[float], Optional[str]]:
        """Parse salary information from text"""
        if not salary_text:
            return None, None, None
            
        import re
        
        # Common salary patterns
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*USD',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    min_sal = float(match.group(1).replace(',', ''))
                    max_sal = float(match.group(2).replace(',', ''))
                    return min_sal, max_sal, 'USD'
                else:
                    salary = float(match.group(1).replace(',', ''))
                    return None, salary, 'USD'
        
        return None, None, None
    
    def normalize_location(self, location: str) -> str:
        """Normalize location string"""
        import re
        
        if not location:
            return ""
        
        # Clean up common location formats
        location = location.strip()
        location = re.sub(r'\s+', ' ', location)
        
        # Handle remote indicators
        remote_keywords = ['remote', 'anywhere', 'distributed', 'work from home', 'wfh']
        if any(keyword in location.lower() for keyword in remote_keywords):
            return "Remote"
        
        return location
    
    def detect_experience_level(self, title: str, description: str = "") -> Optional[str]:
        """Detect experience level from job title and description"""
        import re
        
        title_lower = title.lower()
        text = f"{title} {description}".lower()
        
        # Check for senior/principal keywords first (highest priority)
        if any(re.search(rf'\b{word}\b', title_lower) for word in ['principal', 'staff', 'chief', 'head of', 'director']):
            return 'Principal'
        elif any(re.search(rf'\b{word}\b', title_lower) for word in ['senior', 'sr', 'lead', 'architect', 'manager']):
            return 'Senior'
        
        # Check for internship keywords (using word boundaries to avoid false matches)
        elif any(re.search(rf'\b{word}\b', title_lower) for word in ['intern', 'internship', 'student']):
            return 'Internship'
        
        # Check for entry level keywords
        elif any(re.search(rf'\b{word}\b', title_lower) for word in ['entry', 'junior', 'jr', 'associate', 'new grad', 'graduate']):
            return 'Entry'
        
        # Check for mid-level keywords
        elif any(re.search(rf'\b{word}\b', title_lower) for word in ['mid', 'intermediate', 'experienced']):
            return 'Mid'
        
        return 'Mid'  # Default to mid-level
    
    def detect_remote_type(self, location: str, description: str = "") -> str:
        """Detect if job is remote, hybrid, or on-site"""
        text = f"{location} {description}".lower()
        
        if any(word in text for word in ['remote', 'anywhere', 'distributed']):
            return 'Remote'
        elif any(word in text for word in ['hybrid', 'flexible']):
            return 'Hybrid'
        else:
            return 'On-site'
    
    @abstractmethod
    def get_job_listings_urls(self) -> List[str]:
        """Get list of job listing URLs to scrape"""
        pass
    
    @abstractmethod
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual job listing page"""
        pass
    
    def _scrape_single_job(self, url_with_index: tuple) -> Optional[JobData]:
        """Helper method to scrape a single job (for concurrent processing)"""
        url, index, total = url_with_index
        try:
            logger.info(f"Scraping job {index+1}/{total}: {url}")
            job_data = self.parse_job_listing(url)
            
            # Small delay to be respectful to the server
            time.sleep(0.1)
            
            return job_data
        except Exception as e:
            logger.error(f"Error scraping job {url}: {e}")
            return None
    
    def scrape_all_jobs(self, max_workers: int = 10) -> List[JobData]:
        """Main method to scrape all jobs from the company using concurrent processing"""
        logger.info(f"Starting scrape for {self.company_name}")
        
        # Get all job listing URLs
        job_urls = self.get_job_listings_urls()
        logger.info(f"Found {len(job_urls)} job listings for {self.company_name}")
        
        if not job_urls:
            return []
        
        # Prepare URLs with index information for progress tracking
        urls_with_index = [(url, i, len(job_urls)) for i, url in enumerate(job_urls)]
        
        jobs = []
        
        # Use ThreadPoolExecutor for concurrent scraping
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info(f"Starting concurrent scraping with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_url = {executor.submit(self._scrape_single_job, url_info): url_info[0] 
                           for url_info in urls_with_index}
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_url):
                completed += 1
                url = future_to_url[future]
                try:
                    job_data = future.result()
                    if job_data:
                        jobs.append(job_data)
                    
                    # Log progress every 10 completed jobs
                    if completed % 10 == 0:
                        logger.info(f"Progress: {completed}/{len(job_urls)} jobs processed")
                        
                except Exception as e:
                    logger.error(f"Error processing job {url}: {e}")
        
        logger.info(f"Successfully scraped {len(jobs)} jobs from {self.company_name}")
        return jobs 