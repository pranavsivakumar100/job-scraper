# PostgreSQL Setup Guide

## 🎉 Migration Complete!

Your job scraper has been successfully migrated from SQLite to PostgreSQL!

## 📊 Migration Summary
- **Total Jobs Migrated**: 908 jobs
- **Apple Jobs**: 208
- **NVIDIA Jobs**: 700
- **Database**: PostgreSQL 17.4

## 🚀 Quick Start

### Option 1: Use the Startup Script (Recommended)
```bash
./start_postgres.sh
```

### Option 2: Manual Start
```bash
# Start PostgreSQL
pg_ctl -D ~/postgres_data start

# Set environment variable
export DATABASE_URL="postgresql://pranavsivakumar@localhost:5432/job_scraper"

# Start API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 PostgreSQL Management

### Start PostgreSQL Server
```bash
pg_ctl -D ~/postgres_data start
```

### Stop PostgreSQL Server
```bash
pg_ctl -D ~/postgres_data stop
```

### Check PostgreSQL Status
```bash
pg_isready
```

### Connect to Database
```bash
psql -d job_scraper
```

### Useful SQL Queries
```sql
-- Check total jobs
SELECT COUNT(*) FROM job_listings;

-- Jobs by company
SELECT company, COUNT(*) FROM job_listings GROUP BY company;

-- Recent jobs
SELECT company, title, posted_date FROM job_listings ORDER BY posted_date DESC LIMIT 10;

-- Jobs with salary info
SELECT company, title, salary_min, salary_max FROM job_listings WHERE salary_min IS NOT NULL;
```

## 🌐 API Endpoints

With PostgreSQL, all your existing API endpoints work the same:

- **Health Check**: `http://localhost:8000/health`
- **Companies**: `http://localhost:8000/companies`
- **Jobs**: `http://localhost:8000/jobs`
- **API Docs**: `http://localhost:8000/docs`

## 📈 Performance Benefits

PostgreSQL provides several advantages over SQLite:

1. **Better Performance**: Faster queries on large datasets
2. **Concurrent Access**: Multiple connections without locking
3. **Advanced Indexing**: Better search performance
4. **Full-Text Search**: Better job description searching
5. **Analytics**: Advanced aggregation and reporting
6. **Scalability**: Ready for production deployment

## 🔄 Re-running Migration

If you need to re-run the migration:

```bash
python migrate_to_postgres.py
```

The script is safe to run multiple times - it won't create duplicates.

## 🐛 Troubleshooting

### PostgreSQL Won't Start
```bash
# Check if data directory exists
ls ~/postgres_data

# Reinitialize if needed
rm -rf ~/postgres_data
initdb -D ~/postgres_data
pg_ctl -D ~/postgres_data start
createdb job_scraper
```

### Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready

# Check if database exists
psql -l | grep job_scraper

# Recreate database if needed
dropdb job_scraper
createdb job_scraper
python migrate_to_postgres.py
```

### Environment Variable Issues
```bash
# Check current setting
echo $DATABASE_URL

# Set for current session
export DATABASE_URL="postgresql://pranavsivakumar@localhost:5432/job_scraper"

# Add to your shell profile for persistence
echo 'export DATABASE_URL="postgresql://pranavsivakumar@localhost:5432/job_scraper"' >> ~/.zshrc
```

## 📦 Dependencies

The following packages were added for PostgreSQL support:
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `sqlalchemy==2.0.25` - ORM (already existed)
- `tqdm==4.66.1` - Progress bars for migration

## 🎯 Next Steps

1. **Test Your Frontend**: Connect your React frontend to the PostgreSQL-powered API
2. **Add Indexes**: Optimize performance with database indexes
3. **Backup Strategy**: Set up regular database backups
4. **Production Deployment**: Consider hosted PostgreSQL for production

## 📝 Notes

- Your original SQLite database (`data/jobs.db`) is preserved
- PostgreSQL data is stored in `~/postgres_data/`
- Migration script is idempotent (safe to run multiple times)
- All existing API functionality remains unchanged 