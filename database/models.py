from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os

Base = declarative_base()

class JobListing(Base):
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    location = Column(String(100), index=True)
    remote_type = Column(String(50), index=True)  # Remote, Hybrid, On-site
    department = Column(String(100), index=True)
    experience_level = Column(String(50), index=True)  # Entry, Mid, Senior, Staff, Principal
    employment_type = Column(String(50), index=True)  # Full-time, Part-time, Contract, Internship
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(10))
    description = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    url = Column(String(500), unique=True, nullable=False)
    posted_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company,
            'title': self.title,
            'location': self.location,
            'remote_type': self.remote_type,
            'department': self.department,
            'experience_level': self.experience_level,
            'employment_type': self.employment_type,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'description': self.description,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'url': self.url,
            'posted_date': self.posted_date.isoformat() if self.posted_date is not None else None,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date is not None else None,
            'is_active': self.is_active
        }

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    careers_url = Column(String(500), nullable=False)
    logo_url = Column(String(500))
    industry = Column(String(100))
    headquarters = Column(String(100))
    size = Column(String(50))  # Startup, Medium, Large, Enterprise
    last_scraped = Column(DateTime)
    is_active = Column(Boolean, default=True)
    scraping_config = Column(Text)  # JSON config for scraping parameters

# Database setup
def get_database_url():
    return os.getenv("DATABASE_URL", "sqlite:///./data/jobs.db")

def create_tables():
    engine = create_engine(get_database_url())
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal() 