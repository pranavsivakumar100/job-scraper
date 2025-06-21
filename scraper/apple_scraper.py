from .base_scraper import BaseScraper, JobData, logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from typing import List, Optional
from datetime import datetime

class AppleScraper(BaseScraper):
    """Scraper for Apple careers"""
    
    def __init__(self):
        super().__init__(
            company_name="Apple",
            base_url="https://jobs.apple.com",
            use_playwright=False  # Try requests first, fallback to playwright if needed
        )
    
    def get_job_listings_urls(self) -> List[str]:
        """Get all job listing URLs from Apple careers"""
        job_urls = []
        
        # Apple jobs search page
        search_url = "https://jobs.apple.com/en-us/search"
        
        try:
            # Get the main jobs search page
            content = self.get_page_content(search_url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for job detail links
                job_links = soup.find_all('a', href=re.compile(r'/details/\d+'))
                
                for link in job_links:
                    href = link.get('href', '')
                    if href and 'locationPicker' not in href:  # Skip location picker pages
                        # Clean up the href - remove query parameters for deduplication
                        clean_href = href.split('?')[0]
                        job_url = urljoin(self.base_url, clean_href)
                        job_urls.append(job_url)
                
                logger.info(f"Found {len(job_urls)} job URLs from search page")
                
                # Also try specific team search URLs from Apple career pages
                search_params = [
                    # Software and Services teams
                    "?location=United-States-USA&team=Apps-and-Frameworks-SFTWR-AF",
                    "?location=United-States-USA&team=Cloud-and-Infrastructure-SFTWR-CLD",
                    "?location=United-States-USA&team=Core-Operating-Systems-SFTWR-COS",
                    "?location=United-States-USA&team=DevOps-and-Site-Reliability-SFTWR-DSR",
                    "?location=United-States-USA&team=Engineering-Project-Management-SFTWR-EPM",
                    "?location=United-States-USA&team=Information-Systems-and-Technology-SFTWR-IST",
                    "?location=United-States-USA&team=Security-and-Privacy-SFTWR-SP",
                    "?location=United-States-USA&team=Software-Quality-Automation-and-Tools-SFTWR-SQAT",
                    "?location=United-States-USA&team=Wireless-Software-SFTWR-WS",
                    
                    # Machine Learning and AI teams
                    "?location=united-states-USA&team=machine-learning-infrastructure-MLAI-MLI",
                    "?location=united-states-USA&team=deep-learning-and-reinforcement-learning-MLAI-DLRL",
                    "?location=united-states-USA&team=natural-language-processing-and-speech-technologies-MLAI-NLP",
                    "?location=united-states-USA&team=computer-vision-MLAI-CV",
                    "?location=united-states-USA&team=applied-research-MLAI-AR",
                    
                    # Internships
                    "?team=Internships-STDNT-INTRN",  # Student Internships
                    
                    # General searches
                    "?team=SFTWR",  # Software and Services
                    "?team=HRDWR",  # Hardware
                    "?team=MKTG",   # Marketing
                    "?location=united-states-USA"
                ]
                
                for param in search_params:
                    try:
                        param_url = search_url + param
                        content = self.get_page_content(param_url)
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            param_links = soup.find_all('a', href=re.compile(r'/details/\d+'))
                            
                            for link in param_links:
                                href = link.get('href', '')
                                if href and 'locationPicker' not in href:  # Skip location picker pages
                                    clean_href = href.split('?')[0]
                                    job_url = urljoin(self.base_url, clean_href)
                                    job_urls.append(job_url)
                    except Exception as e:
                        logger.debug(f"Error with search parameter {param}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error fetching Apple job URLs: {e}")
        
        # Remove duplicates and return
        unique_urls = list(set(job_urls))
        logger.info(f"Found {len(unique_urls)} unique Apple job URLs")
        return unique_urls
    
    def parse_job_listing(self, url: str) -> Optional[JobData]:
        """Parse individual Apple job listing"""
        content = self.get_page_content(url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        try:
            # Extract job title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract location - Apple uses specific class for location
            location_elem = soup.find('div', class_='jobdetails-jobdetailheader-location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            location = self.normalize_location(location)
            
            # Extract job description from the main description div
            description = ""
            desc_elem = soup.find('div', id='jobdetails-jobdescription')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # If no description, try job summary
            if not description:
                summary_elem = soup.find('div', id='jobdetails-jobsummary')
                if summary_elem:
                    description = summary_elem.get_text(strip=True)
            
            # Extract qualifications
            requirements = ""
            
            # Minimum qualifications
            min_quals = soup.find('div', id='jobdetails-minimumqualifications')
            if min_quals:
                requirements += "Minimum Qualifications:\n" + min_quals.get_text(strip=True) + "\n\n"
            
            # Preferred qualifications
            pref_quals = soup.find('div', id='jobdetails-preferredqualifications')
            if pref_quals:
                requirements += "Preferred Qualifications:\n" + pref_quals.get_text(strip=True)
            
            requirements = requirements.strip()
            
            # Extract team/department - look in job summary or description for team info
            department = None
            if description:
                # Look for team mentions in the description
                team_patterns = [
                    r'(\w+\s+team)',
                    r'join\s+(?:the\s+)?(\w+\s+\w+)\s+team',
                    r'(\w+\s+(?:engineering|software|hardware|marketing))',
                ]
                for pattern in team_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        department = match.group(1).title()
                        break
            
            # If we didn't get much content, this might be a redirect or login page
            if not description or len(description) < 50:
                logger.warning(f"Limited content found for Apple job: {url}")
                # Try to extract from JSON-LD or other structured data
                json_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'title' in data:
                            title = data.get('title', title)
                            description = data.get('description', description)
                            location = data.get('jobLocation', {}).get('address', {}).get('addressLocality', location)
                    except:
                        continue
            
            # Extract posting date from JSON data on the page
            posted_date = None
            
            # First try to extract from JSON data embedded in the page
            try:
                # Look for the JSON data containing posting information
                json_pattern = r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.+?)"\);'
                json_match = re.search(json_pattern, content, re.DOTALL)
                
                if json_match:
                    # Decode the JSON string (it's escaped)
                    json_str = json_match.group(1)
                    # Unescape the JSON string
                    json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                    
                    try:
                        import json
                        data = json.loads(json_str)
                        
                        # Navigate to the posting date in the JSON structure
                        if 'loaderData' in data and 'jobDetails' in data['loaderData']:
                            job_details = data['loaderData']['jobDetails']
                            if 'jobsData' in job_details:
                                posting_date_str = job_details['jobsData'].get('postingDate')
                                if posting_date_str:
                                    # Parse the date - format like "Jun 17, 2025"
                                    try:
                                        posted_date = datetime.strptime(posting_date_str, '%b %d, %Y')
                                        logger.debug(f"Extracted posting date from JSON: {posted_date}")
                                    except ValueError as e:
                                        logger.warning(f"Could not parse posting date '{posting_date_str}' from JSON: {e}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"Could not parse JSON data for posting date: {e}")
            except Exception as e:
                logger.debug(f"Error extracting posting date from JSON: {e}")
            
            # Fallback: try to extract from HTML div
            if not posted_date:
                posting_date_div = soup.find('div', id='jobdetails-postingdate')
                if posting_date_div:
                    date_text = posting_date_div.get_text().strip()
                    # Extract date using regex - format like "Posted: Jun 18, 2025"
                    date_match = re.search(r'([A-Za-z]{3} \d{1,2}, \d{4})', date_text)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            posted_date = datetime.strptime(date_str, '%b %d, %Y')
                            logger.debug(f"Extracted posting date from HTML: {posted_date}")
                        except ValueError as e:
                            logger.warning(f"Could not parse posting date '{date_str}' for {url}: {e}")
            
            # Detect employment type with word boundaries to avoid false matches
            employment_type = "Full-time"  # Default for Apple
            title_lower = title.lower()
            
            if re.search(r'\b(intern|internship)\b', title_lower):
                employment_type = "Internship"
            elif re.search(r'\b(contract|contractor|temporary|temp)\b', f"{title_lower} {description.lower()}"):
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
            logger.error(f"Error parsing Apple job {url}: {e}")
            return None 