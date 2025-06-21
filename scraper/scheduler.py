#!/usr/bin/env python3
"""
Automated job scraper scheduler with incremental updates
Runs scraping twice daily at 12 PM and 12 AM
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import AppleScraper, JobData
from scraper.nvidia_scraper import NvidiaScraper
from database.models import JobListing, create_tables, get_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapeStats:
    """Statistics for a scraping run"""
    company: str
    scraped: int
    saved: int
    skipped: int
    errors: int
    duration: float
    last_run: datetime

class IncrementalJobScheduler:
    """Scheduler for automated job scraping with incremental updates"""
    
    def __init__(self):
        self.scrapers = {
            'Apple': AppleScraper(),
            'NVIDIA': NvidiaScraper(),
        }
        
        # Create tables if they don't exist
        create_tables()
        
        # Track last successful scrape times
        self.last_scrape_times = {}
        self._load_last_scrape_times()
    
    def _load_last_scrape_times(self):
        """Load last scrape times from database"""
        session = get_session()
        try:
            for company in self.scrapers.keys():
                # Get the most recent scrape time for each company
                last_job = session.query(JobListing)\
                    .filter(JobListing.company == company)\
                    .order_by(desc(JobListing.scraped_date))\
                    .first()
                
                if last_job:
                    self.last_scrape_times[company] = last_job.scraped_date
                    logger.info(f"Last scrape for {company}: {last_job.scraped_date}")
                else:
                    # If no previous scrapes, set to 30 days ago to get recent jobs
                    self.last_scrape_times[company] = datetime.utcnow() - timedelta(days=30)
                    logger.info(f"No previous scrapes for {company}, setting to 30 days ago")
        finally:
            session.close()
    
    def _get_existing_job_urls(self, company: str) -> set:
        """Get existing job URLs for a company to avoid duplicates"""
        session = get_session()
        try:
            existing_urls = session.query(JobListing.url)\
                .filter(JobListing.company == company)\
                .all()
            return {url[0] for url in existing_urls}
        finally:
            session.close()
    
    def _clean_old_jobs(self, days_to_keep: int = 60):
        """Remove jobs older than specified days to keep database clean"""
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = session.query(JobListing)\
                .filter(JobListing.posted_date < cutoff_date)\
                .delete()
            
            session.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old jobs older than {days_to_keep} days")
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning old jobs: {e}")
        finally:
            session.close()
    
    def _save_jobs_to_db(self, jobs: List[JobData], existing_urls: set) -> Dict[str, int]:
        """Save job listings to database with duplicate checking"""
        session = get_session()
        stats = {'saved': 0, 'skipped': 0, 'errors': 0}
        
        try:
            for job_data in jobs:
                try:
                    # Skip if URL already exists
                    if job_data.url in existing_urls:
                        stats['skipped'] += 1
                        logger.debug(f"Skipping existing job: {job_data.url}")
                        continue
                    
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
                    stats['saved'] += 1
                    existing_urls.add(job_data.url)  # Add to set to avoid duplicates in same batch
                    
                except IntegrityError:
                    # Job already exists (duplicate URL)
                    session.rollback()
                    stats['skipped'] += 1
                    logger.debug(f"Job already exists: {job_data.url}")
                    continue
                except Exception as e:
                    session.rollback()
                    stats['errors'] += 1
                    logger.error(f"Error saving job {job_data.title}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Database error: {e}")
            stats['errors'] += 1
        finally:
            session.close()
            
        return stats
    
    def _scrape_company_incremental(self, company_name: str) -> ScrapeStats:
        """Scrape jobs from a specific company with incremental updates"""
        start_time = time.time()
        
        if company_name not in self.scrapers:
            logger.error(f"No scraper available for {company_name}")
            return ScrapeStats(company_name, 0, 0, 0, 1, 0, datetime.utcnow())
        
        logger.info(f"Starting incremental scrape for {company_name}")
        scraper = self.scrapers[company_name]
        
        try:
            # Get existing job URLs to avoid duplicates
            existing_urls = self._get_existing_job_urls(company_name)
            logger.info(f"Found {len(existing_urls)} existing jobs for {company_name}")
            
            # Scrape jobs
            jobs = scraper.scrape_all_jobs()
            logger.info(f"Scraped {len(jobs)} jobs from {company_name}")
            
            # Filter out jobs that are too old (older than 30 days)
            recent_jobs = []
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            for job in jobs:
                if job.posted_date and job.posted_date >= cutoff_date:
                    recent_jobs.append(job)
                elif not job.posted_date:
                    # If no posted date, include it (might be new)
                    recent_jobs.append(job)
            
            logger.info(f"Filtered to {len(recent_jobs)} recent jobs (last 30 days)")
            
            # Save to database
            save_stats = self._save_jobs_to_db(recent_jobs, existing_urls)
            
            # Update last scrape time
            self.last_scrape_times[company_name] = datetime.utcnow()
            
            duration = time.time() - start_time
            
            stats = ScrapeStats(
                company=company_name,
                scraped=len(jobs),
                saved=save_stats['saved'],
                skipped=save_stats['skipped'],
                errors=save_stats['errors'],
                duration=duration,
                last_run=datetime.utcnow()
            )
            
            logger.info(
                f"{company_name} scrape complete: "
                f"{stats.scraped} scraped, {stats.saved} saved, "
                f"{stats.skipped} skipped, {stats.errors} errors "
                f"in {duration:.1f}s"
            )
            
            return stats
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error scraping {company_name}: {e}")
            return ScrapeStats(company_name, 0, 0, 0, 1, duration, datetime.utcnow())
    
    def run_scheduled_scrape(self):
        """Run scheduled scrape for all companies"""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled scrape at {datetime.utcnow()}")
        logger.info("=" * 60)
        
        # Clean up old jobs first
        self._clean_old_jobs(days_to_keep=60)
        
        total_stats = {
            'scraped': 0,
            'saved': 0,
            'skipped': 0,
            'errors': 0,
            'companies': 0
        }
        
        # Scrape each company
        for company_name in self.scrapers.keys():
            try:
                stats = self._scrape_company_incremental(company_name)
                total_stats['scraped'] += stats.scraped
                total_stats['saved'] += stats.saved
                total_stats['skipped'] += stats.skipped
                total_stats['errors'] += stats.errors
                total_stats['companies'] += 1
                
                # Add delay between companies to be respectful
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error processing {company_name}: {e}")
                total_stats['errors'] += 1
        
        logger.info("=" * 60)
        logger.info("Scheduled scrape summary:")
        logger.info(f"Companies processed: {total_stats['companies']}")
        logger.info(f"Total jobs scraped: {total_stats['scraped']}")
        logger.info(f"New jobs saved: {total_stats['saved']}")
        logger.info(f"Jobs skipped (duplicates): {total_stats['skipped']}")
        logger.info(f"Errors: {total_stats['errors']}")
        logger.info("=" * 60)
    
    def start_scheduler(self):
        """Start the scheduled job scraping"""
        logger.info("🕐 Starting Tech Job Scraper Scheduler")
        logger.info("📅 Schedule: 12:00 PM and 12:00 AM daily")
        logger.info("⚡ Incremental updates enabled")
        
        # Schedule jobs for 12 PM and 12 AM
        schedule.every().day.at("12:00").do(self.run_scheduled_scrape)
        schedule.every().day.at("00:00").do(self.run_scheduled_scrape)
        
        # Run initial scrape
        logger.info("🚀 Running initial scrape...")
        self.run_scheduled_scrape()
        
        # Keep the scheduler running
        logger.info("🔄 Scheduler is now running. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
    
    def run_manual_scrape(self, company: Optional[str] = None):
        """Run manual scrape for testing"""
        if company:
            if company in self.scrapers:
                stats = self._scrape_company_incremental(company)
                print(f"\nManual scrape results for {company}:")
                print(f"Scraped: {stats.scraped}")
                print(f"Saved: {stats.saved}")
                print(f"Skipped: {stats.skipped}")
                print(f"Errors: {stats.errors}")
                print(f"Duration: {stats.duration:.1f}s")
            else:
                print(f"Unknown company: {company}")
                print(f"Available companies: {list(self.scrapers.keys())}")
        else:
            self.run_scheduled_scrape()

def main():
    """Main entry point"""
    scheduler = IncrementalJobScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            # Start the scheduler
            scheduler.start_scheduler()
        elif command == "run":
            # Run manual scrape
            company = sys.argv[2] if len(sys.argv) > 2 else None
            scheduler.run_manual_scrape(company)
        elif command == "test":
            # Test scrape (same as run but with more verbose output)
            company = sys.argv[2] if len(sys.argv) > 2 else None
            logging.getLogger().setLevel(logging.DEBUG)
            scheduler.run_manual_scrape(company)
        else:
            print("Usage:")
            print("  python scheduler.py start           # Start scheduled scraping")
            print("  python scheduler.py run [company]   # Run manual scrape")
            print("  python scheduler.py test [company]  # Run test scrape with debug output")
            print(f"  Available companies: {list(scheduler.scrapers.keys())}")
    else:
        print("Tech Job Scraper Scheduler")
        print("Usage:")
        print("  python scheduler.py start           # Start scheduled scraping")
        print("  python scheduler.py run [company]   # Run manual scrape")
        print("  python scheduler.py test [company]  # Run test scrape with debug output")
        print(f"  Available companies: {list(scheduler.scrapers.keys())}")

if __name__ == "__main__":
    main() 