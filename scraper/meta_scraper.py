from .base_scraper import BaseScraper, JobData, logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from typing import List, Optional

class MetaScraper(BaseScraper):
    """Scraper for Meta (Facebook) careers"""
    
    def __init__(self):
        super().__init__(
            company_name="Meta",
            base_url="https://www.metacareers.com",
            use_playwright=True
        )
    
    def get_job_listings_urls(self) -> List[str]:
        """Get all job listing URLs from Meta careers"""
        job_urls = []
        
        # Meta careers search URL
        search_url = "https://www.metacareers.com/jobs/"
        
        try:
            # Try to get the main jobs page and extract links
            content = self.get_page_content(search_url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for job links
                job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+'))
                
                for link in job_links:
                    job_url = urljoin(self.base_url, link['href'])
                    job_urls.append(job_url)
                
                # Also check for API endpoints or AJAX calls
                # Meta often uses GraphQL APIs for job listings
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and 'job' in script.string.lower():
                        # Extract job IDs from script content
                        job_ids = re.findall(r'"job[_-]?id["\s:]+(\d+)', script.string)
                        for job_id in job_ids:
                            job_url = f"https://www.metacareers.com/jobs/{job_id}/"
                            job_urls.append(job_url)
                            
        except Exception as e:
            logger.error(f"Error fetching Meta job URLs: {e}")
        
        return list(set(job_urls))
    
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual Meta job listing"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title
            title_elem = soup.find('h1') or \
                        soup.find('[data-testid="job-title"]') or \
                        soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract location
            location_elem = soup.find('[data-testid="job-location"]') or \
                          soup.find('div', string=re.compile('location', re.I))
            
            if location_elem:
                if hasattr(location_elem, 'get_text'):
                    location = location_elem.get_text(strip=True)
                else:
                    parent = location_elem.find_parent()
                    location = parent.get_text(strip=True) if parent else ""
            else:
                location = ""
            
            location = self.normalize_location(location)
            
            # Extract job description
            description_elem = soup.find('[data-testid="job-description"]') or \
                             soup.find('div', class_=re.compile('description')) or \
                             soup.find('section', class_=re.compile('content'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract requirements
            requirements = ""
            req_headers = soup.find_all(string=re.compile('requirements|qualifications|minimum|preferred', re.I))
            
            for header in req_headers:
                parent = header.find_parent()
                if parent:
                    # Look for the next sibling or list
                    next_elem = parent.find_next_sibling()
                    if next_elem:
                        requirements += next_elem.get_text(strip=True) + " "
            
            # Extract team/department
            department = None
            team_elem = soup.find(string=re.compile('team|department|organization', re.I))
            if team_elem:
                parent = team_elem.find_parent()
                if parent:
                    department = parent.get_text(strip=True)
            
            # Extract employment type
            employment_type = "Full-time"
            if re.search(r'intern|internship', title.lower()):
                employment_type = "Internship"
            elif re.search(r'contract|contractor', description.lower()):
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
            logger.error(f"Error parsing Meta job {url}: {e}")
            return None 