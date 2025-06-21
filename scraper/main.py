#!/usr/bin/env python3
"""
Main scraper coordinator for tech job listings
"""

import os
import sys
import logging
from datetime import datetime
from typing import List
import time

try:
    import schedule  # type: ignore
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import AppleScraper, JobData
from scraper.nvidia_scraper import NvidiaScraper
from database.models import JobListing, create_tables, get_session
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobScrapeCoordinator:
    """Coordinates scraping for multiple tech companies"""
    
    def __init__(self):
        self.scrapers = {
            'Apple': AppleScraper(),
            'NVIDIA': NvidiaScraper(),
        }
        
        # Create tables if they don't exist
        create_tables()
    
    def save_jobs_to_db(self, jobs: List[JobData]) -> int:
        """Save job listings to database"""
        session = get_session()
        saved_count = 0
        
        try:
            for job_data in jobs:
                try:
                    # Convert JobData to JobListing model
                    job_listing = JobListing(
                        company=job_data.company,
                        title=job_data.title,
                        location=job_data.location,
                        remote_type=job_data.remote_type,
                        department=job_data.department,
                        experience_level=job_data.experience_level,
                        employment_type=job_data.employment_type,
                        salary_min=job_data.salary_min,
                        salary_max=job_data.salary_max,
                        salary_currency=job_data.salary_currency,
                        description=job_data.description,
                        requirements=job_data.requirements,
                        benefits=job_data.benefits,
                        url=job_data.url,
                        posted_date=job_data.posted_date,
                        scraped_date=datetime.utcnow()
                    )
                    
                    session.add(job_listing)
                    session.commit()
                    saved_count += 1
                    
                except IntegrityError:
                    # Job already exists (duplicate URL)
                    session.rollback()
                    logger.debug(f"Job already exists: {job_data.url}")
                    continue
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error saving job {job_data.title}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Database error: {e}")
        finally:
            session.close()
            
        return saved_count
    
    def scrape_company(self, company_name: str) -> List[JobData]:
        """Scrape jobs from a specific company"""
        if company_name not in self.scrapers:
            logger.error(f"No scraper available for {company_name}")
            return []
        
        logger.info(f"Starting scrape for {company_name}")
        scraper = self.scrapers[company_name]
        
        try:
            jobs = scraper.scrape_all_jobs()
            logger.info(f"Successfully scraped {len(jobs)} jobs from {company_name}")
            return jobs
        except Exception as e:
            logger.error(f"Error scraping {company_name}: {e}")
            return []
    
    def scrape_all_companies(self) -> dict:
        """Scrape jobs from all configured companies"""
        results = {}
        total_jobs = 0
        total_saved = 0
        
        logger.info("Starting full scrape of all companies")
        
        for company_name in self.scrapers.keys():
            try:
                jobs = self.scrape_company(company_name)
                if jobs:
                    saved_count = self.save_jobs_to_db(jobs)
                    results[company_name] = {
                        'scraped': len(jobs),
                        'saved': saved_count
                    }
                    total_jobs += len(jobs)
                    total_saved += saved_count
                    
                    logger.info(f"{company_name}: {len(jobs)} scraped, {saved_count} saved")
                else:
                    results[company_name] = {'scraped': 0, 'saved': 0}
                    
            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")
                results[company_name] = {'scraped': 0, 'saved': 0, 'error': str(e)}
        
        logger.info(f"Scraping complete: {total_jobs} total jobs scraped, {total_saved} saved to database")
        return results
    
    def run_scheduled_scraping(self, interval_hours: int = 6):
        """Run scraping on a schedule"""
        if not SCHEDULE_AVAILABLE:
            logger.error("Schedule library not available. Install it with: pip install schedule")
            return
            
        logger.info(f"Starting scheduled scraping every {interval_hours} hours")
        
        # Schedule the job
        schedule.every(interval_hours).hours.do(self.scrape_all_companies)
        
        # Run initial scrape
        self.scrape_all_companies()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    coordinator = JobScrapeCoordinator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "schedule":
            # Run on schedule
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 6
            coordinator.run_scheduled_scraping(interval)
        elif sys.argv[1] in coordinator.scrapers.keys():
            # Run specific company
            company = sys.argv[1]
            jobs = coordinator.scrape_company(company)
            saved = coordinator.save_jobs_to_db(jobs)
            print(f"Scraped {len(jobs)} jobs from {company}, saved {saved} to database")
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print(f"Available companies: {list(coordinator.scrapers.keys())}")
    else:
        # Run all companies once
        results = coordinator.scrape_all_companies()
        print("\nScraping Results:")
        for company, stats in results.items():
            print(f"  {company}: {stats['scraped']} scraped, {stats['saved']} saved")

if __name__ == "__main__":
    main() 