from .base_scraper import BaseScraper, JobData, logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from typing import List, Optional

class AmazonScraper(BaseScraper):
    """Scraper for Amazon careers"""
    
    def __init__(self):
        super().__init__(
            company_name="Amazon",
            base_url="https://www.amazon.jobs",
            use_playwright=True
        )
    
    def get_job_listings_urls(self) -> List[str]:
        """Get all job listing URLs from Amazon careers"""
        job_urls = []
        
        # Amazon careers search URL
        search_url = "https://www.amazon.jobs/en/search.json"
        
        try:
            # Parameters for tech jobs
            params = {
                'category[]': 'software-development',
                'country[]': 'US',
                'sort': 'relevant',
                'radius': '24km',
                'limit': 100
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                
                for job in jobs:
                    job_id = job.get('id_icims')
                    if job_id:
                        job_url = f"https://www.amazon.jobs/en/jobs/{job_id}"
                        job_urls.append(job_url)
                        
        except Exception as e:
            logger.error(f"Error fetching Amazon job URLs: {e}")
            
            # Fallback to web scraping
            content = self.get_page_content("https://www.amazon.jobs/en/search?category[]=software-development")
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+'))
                
                for link in job_links:
                    job_url = urljoin(self.base_url, link['href'])
                    job_urls.append(job_url)
        
        return list(set(job_urls))
    
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual Amazon job listing"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title
            title_elem = soup.find('h1', class_='title') or \
                        soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract location
            location_elem = soup.find('p', class_='location') or \
                          soup.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            location = self.normalize_location(location)
            
            # Extract job description
            description_elem = soup.find('div', class_='description') or \
                             soup.find('div', class_='job-description')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract basic qualifications
            requirements = ""
            basic_quals = soup.find('div', class_='basic-qualifications')
            if basic_quals:
                requirements += "Basic Qualifications:\n" + basic_quals.get_text(strip=True) + "\n\n"
            
            # Extract preferred qualifications
            pref_quals = soup.find('div', class_='preferred-qualifications')
            if pref_quals:
                requirements += "Preferred Qualifications:\n" + pref_quals.get_text(strip=True)
            
            # Extract department/team
            department = None
            team_elem = soup.find('p', class_='team')
            if team_elem:
                department = team_elem.get_text(strip=True)
            
            # Detect employment type
            employment_type = "Full-time"
            if re.search(r'intern|internship', title.lower()):
                employment_type = "Internship"
            
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
            logger.error(f"Error parsing Amazon job {url}: {e}")
            return None 