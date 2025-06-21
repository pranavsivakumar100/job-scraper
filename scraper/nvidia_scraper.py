import re
import json
import time
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

from .base_scraper import BaseScraper, JobData

logger = logging.getLogger(__name__)

class NvidiaScraper(BaseScraper):
    def __init__(self):
        super().__init__("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com", use_playwright=False)
        self.api_base = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite"
    
    def _is_job_recent(self, posted_on_text: str) -> bool:
        """Check if job was posted within last 30 days based on posting text"""
        if not posted_on_text:
            return False
            
        posted_on_lower = posted_on_text.lower()
        
        # Handle "Posted Today", "Posted Yesterday"
        if "today" in posted_on_lower:
            return True
        elif "yesterday" in posted_on_lower:
            return True
        
        # Handle "Posted X days ago", "Posted X weeks ago"
        import re
        
        # Match patterns like "Posted 5 days ago", "Posted 2 weeks ago"
        days_match = re.search(r'posted\s+(\d+)\s+days?\s+ago', posted_on_lower)
        if days_match:
            days = int(days_match.group(1))
            return days <= 30
        
        weeks_match = re.search(r'posted\s+(\d+)\s+weeks?\s+ago', posted_on_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return weeks <= 4  # Approximately 30 days
        
        # Handle "Posted 30+ days ago" - these are too old
        if "30+" in posted_on_lower or "30 +" in posted_on_lower:
            return False
            
        # If we can't parse it, include it to be safe
        return True

    def _parse_relative_date(self, posted_on_text: str) -> Optional[datetime]:
        """Parse relative date strings like 'Posted Today', 'Posted X days ago' to actual dates"""
        if not posted_on_text:
            return None
        
        text = posted_on_text.lower().strip()
        now = datetime.now()
        
        # Handle "Posted Today"
        if "today" in text:
            return now.replace(hour=9, minute=0, second=0, microsecond=0)  # Assume posted at 9 AM
        
        # Handle "Posted Yesterday"
        if "yesterday" in text:
            return (now - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Handle "Posted X days ago"
        days_match = re.search(r'posted\s+(\d+)\s+days?\s+ago', text)
        if days_match:
            days = int(days_match.group(1))
            return (now - timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Handle "Posted X weeks ago"
        weeks_match = re.search(r'posted\s+(\d+)\s+weeks?\s+ago', text)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            days = weeks * 7
            return (now - timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Handle "Posted 30+ days ago" - return 30 days ago
        if "30+" in text or "30 +" in text:
            return (now - timedelta(days=30)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Handle "Posted X months ago"
        months_match = re.search(r'posted\s+(\d+)\s+months?\s+ago', text)
        if months_match:
            months = int(months_match.group(1))
            days = months * 30  # Approximate
            return (now - timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # If we can't parse, return None
        return None
    
    def get_job_listings_urls(self) -> List[str]:
        """Get NVIDIA job listing URLs from Workday API (filter for last 30 days)"""
        job_urls = []
        
        try:
            # Start with initial request to get total count and first batch
            initial_payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": 0,
                "searchText": ""
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Get first page to determine total count
            response = self.session.post(
                f"{self.api_base}/jobs",
                json=initial_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                total_jobs = data.get('total', 0)
                logger.info(f"Found {total_jobs} total NVIDIA jobs")
                
                # Extract job URLs from first batch (filter by posting date)
                for job in data.get('jobPostings', []):
                    # Check if job is recent (within 30 days)
                    posted_on = job.get('postedOn', '')
                    if not self._is_job_recent(posted_on):
                        logger.debug(f"Skipping old job: {job.get('title', 'Unknown')} - {posted_on}")
                        continue
                    
                    # bulletFields is a list containing the job ID
                    bullet_fields = job.get('bulletFields', [])
                    if bullet_fields and len(bullet_fields) > 0:
                        job_id = bullet_fields[0]  # First element is the job ID
                        if job_id:
                            # Use correct URL format
                            job_url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/{job_id}"
                            job_urls.append(job_url)
                
                # Get remaining pages if there are more jobs
                if total_jobs > 20:
                    for offset in range(20, min(total_jobs, 1000), 20):  # Limit to 1000 jobs max
                        try:
                            # Add delay to avoid rate limiting
                            time.sleep(0.5)
                            
                            payload = {
                                "appliedFacets": {},
                                "limit": 20,
                                "offset": offset,
                                "searchText": ""
                            }
                            
                            response = self.session.post(
                                f"{self.api_base}/jobs",
                                json=payload,
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                batch_data = response.json()
                                for job in batch_data.get('jobPostings', []):
                                    # Check if job is recent (within 30 days)
                                    posted_on = job.get('postedOn', '')
                                    if not self._is_job_recent(posted_on):
                                        logger.debug(f"Skipping old job: {job.get('title', 'Unknown')} - {posted_on}")
                                        continue
                                    
                                    # bulletFields is a list containing the job ID
                                    bullet_fields = job.get('bulletFields', [])
                                    if bullet_fields and len(bullet_fields) > 0:
                                        job_id = bullet_fields[0]  # First element is the job ID
                                        if job_id:
                                            # Use correct URL format
                                            job_url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/{job_id}"
                                            job_urls.append(job_url)
                                        
                        except Exception as e:
                            logger.warning(f"Error fetching NVIDIA jobs batch at offset {offset}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching NVIDIA job URLs: {e}")
        
        # Remove duplicates
        unique_urls = list(set(job_urls))
        logger.info(f"Found {len(unique_urls)} unique NVIDIA job URLs")
        return unique_urls
    
    def get_all_jobs_data(self) -> List[JobData]:
        """Get all NVIDIA job data directly from API (more efficient than scraping individual pages)"""
        jobs_data = []
        
        try:
            # Start with initial request to get total count and first batch
            initial_payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": 0,
                "searchText": ""
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Get first page to determine total count
            response = self.session.post(
                f"{self.api_base}/jobs",
                json=initial_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                total_jobs = data.get('total', 0)
                logger.info(f"Found {total_jobs} total NVIDIA jobs")
                
                # Process first batch
                jobs_data.extend(self._process_job_batch(data.get('jobPostings', [])))
                
                # Get remaining pages if there are more jobs
                if total_jobs > 20:
                    for offset in range(20, min(total_jobs, 1000), 20):  # Limit to 1000 jobs max
                        try:
                            # Add delay to avoid rate limiting
                            time.sleep(0.5)
                            
                            payload = {
                                "appliedFacets": {},
                                "limit": 20,
                                "offset": offset,
                                "searchText": ""
                            }
                            
                            response = self.session.post(
                                f"{self.api_base}/jobs",
                                json=payload,
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                batch_data = response.json()
                                jobs_data.extend(self._process_job_batch(batch_data.get('jobPostings', [])))
                            else:
                                logger.warning(f"API request failed with status {response.status_code} at offset {offset}")
                                        
                        except Exception as e:
                            logger.warning(f"Error fetching NVIDIA jobs batch at offset {offset}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching NVIDIA job data: {e}")
        
        logger.info(f"Extracted {len(jobs_data)} NVIDIA jobs from API")
        return jobs_data
    
    def _process_job_batch(self, jobs: List[dict]) -> List[JobData]:
        """Process a batch of jobs from the API response"""
        processed_jobs = []
        
        for job in jobs:
            try:
                # Check if job is recent (within 30 days)
                posted_on = job.get('postedOn', '')
                if not self._is_job_recent(posted_on):
                    logger.debug(f"Skipping old job: {job.get('title', 'Unknown')} - {posted_on}")
                    continue
                
                # Extract job data from API response
                title = job.get('title', 'Unknown')
                location = job.get('locationsText', '')
                
                # Get job ID and construct URL
                bullet_fields = job.get('bulletFields', [])
                job_id = bullet_fields[0] if bullet_fields else None
                url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/{job_id}" if job_id else ""
                
                # Parse posting date
                posted_date = None
                if posted_on:
                    try:
                        posted_date = self._parse_relative_date(posted_on)
                    except Exception as e:
                        logger.debug(f"Could not parse posting date '{posted_on}': {e}")
                
                # Normalize location
                location = self.normalize_location(location)
                
                # Detect employment type
                employment_type = "Full-time"  # Default for NVIDIA
                title_lower = title.lower()
                
                if re.search(r'\b(intern|internship)\b', title_lower):
                    employment_type = "Internship"
                elif re.search(r'\b(contract|contractor|temporary|temp)\b', title_lower):
                    employment_type = "Contract"
                elif re.search(r'\b(part.time|part-time)\b', title_lower):
                    employment_type = "Part-time"
                
                # Create JobData object
                job_data = JobData(
                    title=title,
                    company=self.company_name,
                    location=location,
                    url=url,
                    remote_type=self.detect_remote_type(location, ""),
                    department=None,  # Not available in API response
                    experience_level=self.detect_experience_level(title, ""),
                    employment_type=employment_type,
                    description="",  # We'll need to scrape individual pages for this if needed
                    requirements="",  # We'll need to scrape individual pages for this if needed
                    posted_date=posted_date
                )
                
                processed_jobs.append(job_data)
                
            except Exception as e:
                logger.error(f"Error processing NVIDIA job: {e}")
                continue
        
        return processed_jobs
    
    def scrape_all_jobs(self, max_workers: int = 10) -> List[JobData]:
        """Override the base scrape_all_jobs method to use API-based approach"""
        logger.info(f"Starting scrape for {self.company_name}")
        
        # Use API-based approach instead of individual page scraping
        jobs_data = self.get_all_jobs_data()
        
        logger.info(f"Successfully scraped {len(jobs_data)} jobs from {self.company_name}")
        return jobs_data

    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual NVIDIA job listing from Workday (fallback method)"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title - try multiple selectors
            title = "Unknown"
            title_selectors = [
                'h1[data-automation-id="jobPostingHeader"]',
                'h1',
                '[data-automation-id*="title"]',
                'h2',
                '.css-1id7n2j',  # Common Workday title class
                '[role="heading"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract location - try multiple selectors
            location = ""
            location_selectors = [
                '[data-automation-id="jobPostingLocation"]',
                '[data-automation-id*="location"]',
                '.css-1p9biqh',
                'dd[data-automation-id="jobPostingLocation"]',
                '[data-testid*="location"]',
                'span:contains("Location")',
                'div:contains("Location")'
            ]
            
            for selector in location_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        location = elem.get_text(strip=True)
                        # Clean up location text
                        if "location" in location.lower():
                            # Extract actual location from "Location: Santa Clara, CA"
                            location = location.split(":", 1)[-1].strip()
                        break
                except:
                    continue
            
            location = self.normalize_location(location)
            
            # Extract job description - try multiple selectors
            description = ""
            desc_selectors = [
                '[data-automation-id="jobPostingDescription"]',
                '[data-automation-id*="description"]',
                '.css-1t92pv',  # Common Workday description class
                'div[role="document"]',
                '.wd-popup-content'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem and desc_elem.get_text(strip=True):
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Extract requirements/qualifications
            requirements = ""
            
            # Look for qualifications sections
            qual_selectors = [
                '[data-automation-id*="qualifications"]',
                '[data-automation-id*="requirements"]',
                'div:contains("What we need to see")',
                'div:contains("Minimum Requirements")',
                'div:contains("Required Qualifications")'
            ]
            
            for selector in qual_selectors:
                elem = soup.select_one(selector)
                if elem:
                    requirements += elem.get_text(strip=True) + "\n\n"
            
            requirements = requirements.strip()
            
            # Extract department/team info
            department = None
            
            # Look for team/department in job posting details
            dept_elem = soup.find('dd', {'data-automation-id': 'jobPostingCompanyValue'})
            if dept_elem:
                department = dept_elem.get_text(strip=True)
            
            # If no department found, try to extract from title or description
            if not department and description:
                # Look for team mentions
                team_patterns = [
                    r'(\w+\s+(?:team|group|division))',
                    r'join\s+(?:the\s+)?(\w+\s+\w+)\s+team',
                    r'(\w+\s+(?:engineering|software|hardware|ai|ml))',
                ]
                for pattern in team_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        department = match.group(1).title()
                        break
            
            # Extract posting date
            posted_date = None
            date_elem = soup.find('dd', {'data-automation-id': 'jobPostingDateValue'})
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    # Workday typically uses formats like "Posted 30+ Days Ago" or actual dates
                    if 'ago' in date_text.lower():
                        # Handle relative dates - for now, we'll skip these
                        pass
                    else:
                        # Try to parse actual dates
                        date_patterns = [
                            '%B %d, %Y',  # January 15, 2025
                            '%m/%d/%Y',   # 01/15/2025
                            '%Y-%m-%d'    # 2025-01-15
                        ]
                        for pattern in date_patterns:
                            try:
                                posted_date = datetime.strptime(date_text, pattern)
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.debug(f"Could not parse posting date '{date_text}': {e}")
            
            # Detect employment type
            employment_type = "Full-time"  # Default for NVIDIA
            title_lower = title.lower()
            desc_lower = description.lower()
            
            if re.search(r'\b(intern|internship)\b', title_lower):
                employment_type = "Internship"
            elif re.search(r'\b(contract|contractor|temporary|temp)\b', f"{title_lower} {desc_lower}"):
                employment_type = "Contract"
            elif re.search(r'\b(part.time|part-time)\b', title_lower):
                employment_type = "Part-time"
            
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
                requirements=requirements,
                posted_date=posted_date
            )
            
        except Exception as e:
            logger.error(f"Error parsing NVIDIA job {url}: {e}")
            return None 