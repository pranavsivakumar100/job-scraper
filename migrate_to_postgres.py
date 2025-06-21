#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Base, JobListing, Company
from tqdm import tqdm

# Database URLs
SQLITE_URL = "sqlite:///./data/jobs.db"
POSTGRES_URL = "postgresql://pranavsivakumar@localhost:5432/job_scraper"

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    # Create engines
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    # Create tables in PostgreSQL
    print("📋 Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=postgres_engine)
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate Companies
        print("🏢 Migrating companies...")
        companies = sqlite_session.query(Company).all()
        if companies:
            for company in tqdm(companies, desc="Companies"):
                # Check if company already exists
                existing = postgres_session.query(Company).filter_by(name=company.name).first()
                if not existing:
                    new_company = Company(
                        name=company.name,
                        careers_url=company.careers_url,
                        logo_url=company.logo_url,
                        industry=company.industry,
                        headquarters=company.headquarters,
                        size=company.size,
                        last_scraped=company.last_scraped,
                        is_active=company.is_active,
                        scraping_config=company.scraping_config
                    )
                    postgres_session.add(new_company)
            postgres_session.commit()
            print(f"✅ Migrated {len(companies)} companies")
        else:
            print("ℹ️ No companies found to migrate")
        
        # Migrate Job Listings
        print("💼 Migrating job listings...")
        jobs = sqlite_session.query(JobListing).all()
        if jobs:
            batch_size = 100
            for i in tqdm(range(0, len(jobs), batch_size), desc="Job batches"):
                batch = jobs[i:i + batch_size]
                for job in batch:
                    # Check if job already exists
                    existing = postgres_session.query(JobListing).filter_by(url=job.url).first()
                    if not existing:
                        new_job = JobListing(
                            company=job.company,
                            title=job.title,
                            location=job.location,
                            remote_type=job.remote_type,
                            department=job.department,
                            experience_level=job.experience_level,
                            employment_type=job.employment_type,
                            salary_min=job.salary_min,
                            salary_max=job.salary_max,
                            salary_currency=job.salary_currency,
                            description=job.description,
                            requirements=job.requirements,
                            benefits=job.benefits,
                            url=job.url,
                            posted_date=job.posted_date,
                            scraped_date=job.scraped_date,
                            is_active=job.is_active
                        )
                        postgres_session.add(new_job)
                postgres_session.commit()
            print(f"✅ Migrated {len(jobs)} job listings")
        else:
            print("ℹ️ No job listings found to migrate")
        
        # Verify migration
        print("🔍 Verifying migration...")
        pg_companies = postgres_session.query(Company).count()
        pg_jobs = postgres_session.query(JobListing).count()
        
        print(f"📊 Migration Summary:")
        print(f"   Companies: {pg_companies}")
        print(f"   Job Listings: {pg_jobs}")
        
        # Test some queries
        print("🧪 Testing queries...")
        apple_jobs = postgres_session.query(JobListing).filter_by(company='Apple').count()
        nvidia_jobs = postgres_session.query(JobListing).filter_by(company='NVIDIA').count()
        
        print(f"   Apple jobs: {apple_jobs}")
        print(f"   NVIDIA jobs: {nvidia_jobs}")
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_session.rollback()
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()
    
    return True

def test_connection():
    """Test PostgreSQL connection"""
    try:
        engine = create_engine(POSTGRES_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            row = result.fetchone()
            if row:
                version = row[0]
                print(f"✅ PostgreSQL connection successful!")
                print(f"   Version: {version}")
            else:
                print(f"✅ PostgreSQL connection successful!")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 PostgreSQL Migration Tool")
    print("=" * 50)
    
    # Test connection first
    if not test_connection():
        print("💡 Make sure PostgreSQL is running and database exists:")
        print("   pg_ctl -D ~/postgres_data start")
        print("   createdb job_scraper")
        sys.exit(1)
    
    # Run migration
    if migrate_data():
        print("\n🎯 Next steps:")
        print("1. Update your environment to use PostgreSQL:")
        print(f"   export DATABASE_URL='{POSTGRES_URL}'")
        print("2. Restart your API server")
        print("3. Test the application")
    else:
        sys.exit(1) 