from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import json
import os

app = FastAPI(
    title="Tech Jobs Scraper API",
    description="API for accessing scraped tech job listings from multiple companies",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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

# Mock data for demonstration
MOCK_JOBS = [
    {
        "id": 1,
        "company": "Apple",
        "title": "Senior Software Engineer - iOS",
        "location": "Cupertino, CA",
        "remote_type": "Hybrid",
        "department": "Software Engineering",
        "experience_level": "Senior",
        "employment_type": "Full-time",
        "salary_min": 150000.0,
        "salary_max": 200000.0,
        "salary_currency": "USD",
        "description": "Join our iOS team to build amazing user experiences.",
        "requirements": "5+ years iOS development experience",
        "benefits": "Health, dental, vision insurance",
        "url": "https://jobs.apple.com/example1",
        "posted_date": "2024-01-15",
        "scraped_date": "2024-01-16",
        "is_active": True
    },
    {
        "id": 2,
        "company": "NVIDIA",
        "title": "Machine Learning Engineer",
        "location": "Santa Clara, CA",
        "remote_type": "Remote",
        "department": "AI/ML",
        "experience_level": "Mid-level",
        "employment_type": "Full-time",
        "salary_min": 130000.0,
        "salary_max": 180000.0,
        "salary_currency": "USD",
        "description": "Work on cutting-edge AI/ML projects.",
        "requirements": "3+ years ML experience",
        "benefits": "Stock options, flexible hours",
        "url": "https://nvidia.wd5.myworkdayjobs.com/example2",
        "posted_date": "2024-01-14",
        "scraped_date": "2024-01-16",
        "is_active": True
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tech Jobs Scraper API - Vercel Demo", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running on Vercel"}

@app.get("/companies")
async def get_companies():
    """Get list of available companies"""
    companies = {}
    for job in MOCK_JOBS:
        company = job["company"]
        companies[company] = companies.get(company, 0) + 1
    
    return {
        "companies": [{"name": company, "count": count} for company, count in companies.items()]
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
    salary_max: Optional[float] = Query(None, description="Maximum salary")
):
    """Get job listings with filtering and pagination"""
    
    # Filter jobs based on query parameters
    filtered_jobs = MOCK_JOBS.copy()
    
    if company:
        filtered_jobs = [job for job in filtered_jobs if job["company"] == company]
    
    if location:
        filtered_jobs = [job for job in filtered_jobs if location.lower() in job["location"].lower()]
    
    if remote_type:
        filtered_jobs = [job for job in filtered_jobs if job["remote_type"] == remote_type]
    
    if department:
        filtered_jobs = [job for job in filtered_jobs if department.lower() in job["department"].lower()]
    
    if experience_level:
        filtered_jobs = [job for job in filtered_jobs if job["experience_level"] == experience_level]
    
    if employment_type:
        filtered_jobs = [job for job in filtered_jobs if job["employment_type"] == employment_type]
    
    if search:
        search_lower = search.lower()
        filtered_jobs = [
            job for job in filtered_jobs 
            if search_lower in job["title"].lower() or search_lower in job["description"].lower()
        ]
    
    if salary_min:
        filtered_jobs = [
            job for job in filtered_jobs 
            if job["salary_min"] and job["salary_min"] >= salary_min
        ]
    
    if salary_max:
        filtered_jobs = [
            job for job in filtered_jobs 
            if job["salary_max"] and job["salary_max"] <= salary_max
        ]
    
    # Calculate pagination
    total = len(filtered_jobs)
    total_pages = (total + per_page - 1) // per_page
    
    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_jobs = filtered_jobs[start_idx:end_idx]
    
    # Convert dict objects to Pydantic models
    job_responses = [JobListingResponse(**job) for job in paginated_jobs]
    
    return JobListingsResponse(
        jobs=job_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.get("/jobs/{job_id}", response_model=JobListingResponse)
async def get_job(job_id: int):
    """Get a specific job by ID"""
    job = next((job for job in MOCK_JOBS if job["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobListingResponse(**job)

@app.get("/stats/filters", response_model=FilterStats)
async def get_filter_stats(
    company: Optional[str] = Query(None, description="Filter by company")
):
    """Get available filter options"""
    jobs = MOCK_JOBS
    if company:
        jobs = [job for job in jobs if job["company"] == company]
    
    # Extract unique values for each filter
    locations = list(set(job["location"] for job in jobs if job["location"]))
    remote_types = list(set(job["remote_type"] for job in jobs if job["remote_type"]))
    departments = list(set(job["department"] for job in jobs if job["department"]))
    experience_levels = list(set(job["experience_level"] for job in jobs if job["experience_level"]))
    employment_types = list(set(job["employment_type"] for job in jobs if job["employment_type"]))
    companies = list(set(job["company"] for job in jobs))
    
    return FilterStats(
        locations=[{"name": loc, "count": 1} for loc in locations],
        remote_types=[{"name": rt, "count": 1} for rt in remote_types],
        departments=[{"name": dept, "count": 1} for dept in departments],
        experience_levels=[{"name": level, "count": 1} for level in experience_levels],
        employment_types=[{"name": emp_type, "count": 1} for emp_type in employment_types],
        companies=[{"name": company, "count": 1} for company in companies]
    )

@app.get("/stats/summary")
async def get_summary_stats(
    company: Optional[str] = Query(None, description="Filter by company")
):
    """Get summary statistics"""
    jobs = MOCK_JOBS
    if company:
        jobs = [job for job in jobs if job["company"] == company]
    
    return {
        "total_jobs": len(jobs),
        "companies": len(set(job["company"] for job in jobs)),
        "locations": len(set(job["location"] for job in jobs)),
        "remote_jobs": len([job for job in jobs if job["remote_type"] == "Remote"]),
        "hybrid_jobs": len([job for job in jobs if job["remote_type"] == "Hybrid"]),
        "onsite_jobs": len([job for job in jobs if job["remote_type"] == "On-site"])
    }

# For Vercel, we need to export the app as 'app'
# This is the entry point for Vercel's Python runtime 