#!/usr/bin/env python3
"""
Initialize database for Railway deployment
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Base, JobListing, get_session, create_tables
from datetime import datetime

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    engine = create_tables()
    print("Database tables created successfully!")
    
    # Add a sample job if no jobs exist
    session = get_session()
    try:
        job_count = session.query(JobListing).count()
        if job_count == 0:
            print("Adding sample job...")
            sample_job = JobListing(
                company="Sample Company",
                title="Software Engineer",
                location="Remote",
                remote_type="Remote",
                department="Engineering",
                experience_level="Mid-level",
                employment_type="Full-time",
                description="This is a sample job posting to verify the API is working.",
                url="https://example.com/job",
                posted_date=datetime.now(),
                scraped_date=datetime.now(),
                is_active=True
            )
            session.add(sample_job)
            session.commit()
            print("Sample job added successfully!")
        else:
            print(f"Database already has {job_count} jobs")
    except Exception as e:
        print(f"Error adding sample job: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_database() 