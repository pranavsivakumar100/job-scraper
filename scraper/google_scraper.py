from .base_scraper import BaseScraper, JobData, logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from typing import List, Optional

class GoogleScraper(BaseScraper):
    """Scraper for Google/Alphabet careers"""
    
    def __init__(self):
        super().__init__(
            company_name="Google",
            base_url="https://careers.google.com",
            use_playwright=True  # Google uses heavy JS
        )
    
    def get_job_listings_urls(self) -> List[str]:
        """Get all job listing URLs from Google careers"""
        job_urls = []
        
        # Google careers API endpoint
        search_url = "https://careers.google.com/api/v3/search/"
        
        try:
            # Parameters for tech jobs
            params = {
                'distance': 50,
                'hl': 'en_US',
                'jlo': 'en_US',
                'q': '',
                'sort_by': 'relevance'
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                
                for job in jobs:
                    if 'apply_url' in job:
                        job_urls.append(job['apply_url'])
                        
        except Exception as e:
            logger.error(f"Error fetching Google job URLs: {e}")
            
            # Fallback to web scraping
            content = self.get_page_content("https://careers.google.com/jobs/results/")
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                job_links = soup.find_all('a', href=re.compile(r'/jobs/results/\d+'))
                
                for link in job_links:
                    job_url = urljoin(self.base_url, link['href'])
                    job_urls.append(job_url)
        
        return list(set(job_urls))  # Remove duplicates
    
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual Google job listing"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title
            title_elem = soup.find('h2', {'data-automation-id': 'job-title'}) or \
                        soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract location
            location_elem = soup.find('span', {'data-automation-id': 'job-location'}) or \
                          soup.find('div', class_=re.compile('location'))
            location = location_elem.get_text(strip=True) if location_elem else ""
            location = self.normalize_location(location)
            
            # Extract job description
            description_elem = soup.find('div', {'data-automation-id': 'job-description'}) or \
                             soup.find('div', class_=re.compile('description'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract requirements (usually in a specific section)
            requirements_elem = soup.find('div', string=re.compile('requirements|qualifications', re.I))
            if requirements_elem:
                requirements_parent = requirements_elem.find_parent()
                requirements = requirements_parent.get_text(strip=True) if requirements_parent else ""
            else:
                requirements = ""
            
            # Extract department/team
            department = None
            dept_patterns = ['team', 'department', 'division']
            for pattern in dept_patterns:
                dept_elem = soup.find(string=re.compile(pattern, re.I))
                if dept_elem:
                    department = str(dept_elem).strip()
                    break
            
            # Detect employment type
            employment_type = "Full-time"  # Google default
            if re.search(r'intern|internship', title.lower()):
                employment_type = "Internship"
            elif re.search(r'contract|temporary', description.lower()):
                employment_type = "Contract"
            
            return JobData(
                title=title,
                company=self.company_name,
                location=location,
                url=url,
                remote_type=self.detect_remote_type(location, description),
                department=department,
                experience_level=self.detect_experience_level(title, description),
                employment_type=employment_type,
                description=description,
                requirements=requirements
            )
            
        except Exception as e:
            logger.error(f"Error parsing Google job {url}: {e}")
            return None 