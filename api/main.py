from fastapi import FastAPI, HTTPException, Query, Depends  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import JobListing, get_session
from pydantic import BaseModel

app = FastAPI(
    title="Tech Jobs Scraper API",
    description="API for accessing scraped tech job listings from multiple companies with accurate posting dates",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

# Pydantic models for API responses
class JobListingResponse(BaseModel):
    id: int
    company: str
    title: str
    location: str
    remote_type: Optional[str]
    department: Optional[str]
    experience_level: Optional[str]
    employment_type: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    benefits: Optional[str]
    url: str
    posted_date: Optional[str]
    scraped_date: Optional[str]
    is_active: bool

class JobListingsResponse(BaseModel):
    jobs: List[JobListingResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class FilterStats(BaseModel):
    locations: List[dict]
    remote_types: List[dict]
    departments: List[dict]
    experience_levels: List[dict]
    employment_types: List[dict]
    companies: List[dict]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tech Jobs Scraper API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/companies")
async def get_companies(db: Session = Depends(get_db_session)):
    """Get list of available companies"""
    companies = db.query(
        JobListing.company,
        func.count(JobListing.id).label('count')
    ).filter(JobListing.is_active == True).group_by(JobListing.company).all()
    
    return {
        "companies": [{"name": company, "count": count} for company, count in companies]
    }

@app.get("/jobs", response_model=JobListingsResponse)
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Jobs per page"),
    company: Optional[str] = Query(None, description="Filter by company"),
    location: Optional[str] = Query(None, description="Filter by location"),
    remote_type: Optional[str] = Query(None, description="Filter by remote type"),
    department: Optional[str] = Query(None, description="Filter by department"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    salary_min: Optional[float] = Query(None, description="Minimum salary"),
    salary_max: Optional[float] = Query(None, description="Maximum salary"),
    db: Session = Depends(get_db_session)
):
    """Get job listings with filtering and pagination"""
    
    # Base query for active jobs
    from datetime import datetime, timedelta
    
    query = db.query(JobListing).filter(JobListing.is_active == True)
    
    # Apply company filter
    if company:
        query = query.filter(JobListing.company == company)
    
    # Default: show jobs from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    query = query.filter(
        or_(
            JobListing.posted_date >= thirty_days_ago,
            JobListing.posted_date.is_(None)
        )
    )
    
    # Apply filters (remove company filter since we only have Apple)
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    
    if remote_type:
        query = query.filter(JobListing.remote_type == remote_type)
    
    if department:
        query = query.filter(JobListing.department.ilike(f"%{department}%"))
    
    if experience_level:
        query = query.filter(JobListing.experience_level == experience_level)
    
    if employment_type:
        query = query.filter(JobListing.employment_type == employment_type)
    
    if search:
        search_filter = or_(
            JobListing.title.ilike(f"%{search}%"),
            JobListing.description.ilike(f"%{search}%"),
            JobListing.requirements.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if salary_min:
        query = query.filter(
            or_(
                JobListing.salary_min >= salary_min,
                JobListing.salary_max >= salary_min
            )
        )
    
    if salary_max:
        query = query.filter(
            or_(
                JobListing.salary_min <= salary_max,
                JobListing.salary_max <= salary_max
            )
        )
    
    # Get total count
    total = query.count()
    
    # Sort by posting date (latest first), then by ID for consistency
    query = query.order_by(JobListing.posted_date.desc(), JobListing.id.desc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    jobs = query.offset(offset).limit(per_page).all()
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    # Convert to response format
    job_responses = []
    for job in jobs:
        job_dict = job.to_dict()
        job_responses.append(JobListingResponse(**job_dict))
    
    return JobListingsResponse(
        jobs=job_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.get("/jobs/{job_id}", response_model=JobListingResponse)
async def get_job(job_id: int, db: Session = Depends(get_db_session)):
    """Get a specific job by ID"""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_dict = job.to_dict()
    return JobListingResponse(**job_dict)

@app.get("/stats/filters", response_model=FilterStats)
async def get_filter_stats(
    company: Optional[str] = Query(None, description="Filter by company"),
    db: Session = Depends(get_db_session)
):
    """Get statistics for filter options"""
    
    # Filter for jobs posted within the last 30 days
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    base_filter = and_(
        JobListing.is_active == True,
        or_(
            JobListing.posted_date >= thirty_days_ago,
            JobListing.posted_date.is_(None)
        )
    )
    
    # Add company filter
    if company:
        base_filter = and_(base_filter, JobListing.company == company)
    
    # Get location counts
    locations = db.query(
        JobListing.location,
        func.count(JobListing.id).label('count')
    ).filter(
        and_(base_filter, JobListing.location.isnot(None))
    ).group_by(JobListing.location).limit(50).all()
    
    # Get remote type counts
    remote_types = db.query(
        JobListing.remote_type,
        func.count(JobListing.id).label('count')
    ).filter(
        and_(base_filter, JobListing.remote_type.isnot(None))
    ).group_by(JobListing.remote_type).all()
    
    # Get department counts
    departments = db.query(
        JobListing.department,
        func.count(JobListing.id).label('count')
    ).filter(
        and_(base_filter, JobListing.department.isnot(None))
    ).group_by(JobListing.department).limit(30).all()
    
    # Get experience level counts
    experience_levels = db.query(
        JobListing.experience_level,
        func.count(JobListing.id).label('count')
    ).filter(
        and_(base_filter, JobListing.experience_level.isnot(None))
    ).group_by(JobListing.experience_level).all()
    
    # Get employment type counts
    employment_types = db.query(
        JobListing.employment_type,
        func.count(JobListing.id).label('count')
    ).filter(
        and_(base_filter, JobListing.employment_type.isnot(None))
    ).group_by(JobListing.employment_type).all()
    
    # Get company counts (only if no company filter is applied)
    if company:
        companies = []
    else:
        companies = db.query(
            JobListing.company,
            func.count(JobListing.id).label('count')
        ).filter(
            and_(base_filter, JobListing.company.isnot(None))
        ).group_by(JobListing.company).all()
    
    return FilterStats(
        locations=[{"name": l[0], "count": l[1]} for l in locations],
        remote_types=[{"name": r[0], "count": r[1]} for r in remote_types],
        departments=[{"name": d[0], "count": d[1]} for d in departments],
        experience_levels=[{"name": e[0], "count": e[1]} for e in experience_levels],
        employment_types=[{"name": et[0], "count": et[1]} for et in employment_types],
        companies=[{"name": c[0], "count": c[1]} for c in companies]
    )

@app.get("/stats/summary")
async def get_summary_stats(
    company: Optional[str] = Query(None, description="Filter by company"),
    db: Session = Depends(get_db_session)
):
    """Get summary statistics for jobs"""
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    base_filter = and_(
        JobListing.is_active == True,
        or_(
            JobListing.posted_date >= thirty_days_ago,
            JobListing.posted_date.is_(None)
        )
    )
    
    # Add company filter if specified
    if company:
        base_filter = and_(base_filter, JobListing.company == company)
    
    total_jobs = db.query(func.count(JobListing.id)).filter(base_filter).scalar()
    
    # Count distinct companies
    if company:
        total_companies = 1 if total_jobs > 0 else 0
    else:
        total_companies = db.query(func.count(func.distinct(JobListing.company))).filter(base_filter).scalar()
    
    # Recent jobs (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_jobs = db.query(func.count(JobListing.id)).filter(
        and_(base_filter, JobListing.scraped_date >= week_ago)
    ).scalar()
    
    return {
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "recent_jobs": recent_jobs,
        "last_updated": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000) 