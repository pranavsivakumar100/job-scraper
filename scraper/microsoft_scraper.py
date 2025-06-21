from .base_scraper import BaseScraper, JobData, logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from typing import List, Optional

class MicrosoftScraper(BaseScraper):
    """Scraper for Microsoft careers"""
    
    def __init__(self):
        super().__init__(
            company_name="Microsoft",
            base_url="https://careers.microsoft.com",
            use_playwright=True
        )
    
    def get_job_listings_urls(self) -> List[str]:
        """Get all job listing URLs from Microsoft careers"""
        job_urls = []
        
        # Microsoft careers search URL
        search_url = "https://careers.microsoft.com/us/en/search-results"
        
        try:
            # Try API first
            api_url = "https://careers.microsoft.com/rest/v1/search"
            params = {
                'businesscategory': 'Engineering',
                'country': 'United States',
                'l': 'en_us',
                'pg': 1,
                'pgSz': 20
            }
            
            for page in range(1, 6):  # Get first 5 pages
                params['pg'] = page
                response = self.session.get(api_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('data', {}).get('jobs', [])
                    
                    if not jobs:
                        break
                        
                    for job in jobs:
                        job_id = job.get('jobId')
                        if job_id:
                            job_url = f"https://careers.microsoft.com/us/en/job/{job_id}"
                            job_urls.append(job_url)
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error fetching Microsoft job URLs via API: {e}")
            
            # Fallback to web scraping
            content = self.get_page_content(search_url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                job_links = soup.find_all('a', href=re.compile(r'/job/\d+'))
                
                for link in job_links:
                    job_url = urljoin(self.base_url, link['href'])
                    job_urls.append(job_url)
        
        return list(set(job_urls))
    
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual Microsoft job listing"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title
            title_elem = soup.find('h1', {'data-automation-id': 'jobPostingHeader'}) or \
                        soup.find('h1') or soup.find('[data-test="job-title"]')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract location
            location_elem = soup.find('[data-automation-id="job-location"]') or \
                          soup.find('[data-test="job-location"]')
            location = location_elem.get_text(strip=True) if location_elem else ""
            location = self.normalize_location(location)
            
            # Extract job description
            description_elem = soup.find('[data-automation-id="jobPostingDescription"]') or \
                             soup.find('div', class_=re.compile('description|content'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract qualifications/requirements
            qual_headers = soup.find_all(string=re.compile('qualifications|requirements|skills', re.I))
            requirements = ""
            
            for header in qual_headers:
                parent = header.find_parent()
                if parent:
                    sibling = parent.find_next_sibling()
                    if sibling:
                        requirements += sibling.get_text(strip=True) + " "
            
            # Extract department/role family
            department = None
            role_elem = soup.find('[data-automation-id="role-family"]') or \
                       soup.find(string=re.compile('role family|department', re.I))
            if role_elem:
                if hasattr(role_elem, 'get_text'):
                    department = role_elem.get_text(strip=True)
                else:
                    department = str(role_elem).strip()
            
            # Extract employment type
            employment_type = "Full-time"
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
                requirements=requirements.strip()
            )
            
        except Exception as e:
            logger.error(f"Error parsing Microsoft job {url}: {e}")
            return None 