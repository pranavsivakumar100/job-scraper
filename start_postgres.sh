#!/bin/bash

# Start PostgreSQL Migration & API Script
echo "🚀 Starting Job Scraper with PostgreSQL"
echo "========================================"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "📋 Starting PostgreSQL server..."
    pg_ctl -D ~/postgres_data -l ~/postgres_data/logfile start
    sleep 2
fi

# Check if database exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw job_scraper; then
    echo "🗄️ Creating job_scraper database..."
    createdb job_scraper
fi

# Set environment variable
export DATABASE_URL="postgresql://pranavsivakumar@localhost:5432/job_scraper"

# Start API server
echo "🌐 Starting API server on http://localhost:8000"
echo "   Dashboard: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""
echo "📊 Database Stats:"
echo "   Companies: $(psql -d job_scraper -t -c 'SELECT COUNT(*) FROM companies;' 2>/dev/null | xargs || echo 'N/A')"
echo "   Jobs: $(psql -d job_scraper -t -c 'SELECT COUNT(*) FROM job_listings;' 2>/dev/null | xargs || echo 'N/A')"
echo ""

# Start the API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload 