# 🕐 Tech Job Scraper - Automated Scheduler Guide

This guide will help you set up automated job scraping that runs twice daily at 12 PM and 12 AM with energy-efficient incremental updates.

## ✨ Features

- **🕐 Automated Schedule**: Runs at 12:00 PM and 12:00 AM daily
- **⚡ Incremental Updates**: Only scrapes new jobs, avoiding full re-scraping
- **🔄 Duplicate Prevention**: Skips existing jobs to save energy and time
- **🧹 Auto Cleanup**: Removes jobs older than 60 days
- **📊 Detailed Logging**: Comprehensive logs for monitoring
- **🛡️ Error Recovery**: Automatic restart on failures
- **🎯 Smart Filtering**: Only processes jobs from last 30 days

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script
./setup_scheduler.sh

# The script will:
# 1. Install dependencies
# 2. Test the scheduler
# 3. Create systemd service
# 4. Start the service
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip3 install -r requirements.txt
python3 -m playwright install

# Test the scheduler
python3 scraper/scheduler.py test Apple

# Create and start service (requires sudo)
sudo cp job-scraper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable job-scraper
sudo systemctl start job-scraper
```

## 📅 Schedule Details

The scheduler runs **twice daily**:
- **12:00 PM (noon)** - Midday scrape to catch new postings
- **12:00 AM (midnight)** - End-of-day scrape for final updates

### Why These Times?
- **12 PM**: Many companies post jobs during business hours
- **12 AM**: Catches any end-of-day postings and ensures daily coverage

## ⚡ Energy Efficiency Features

### Incremental Scraping
- **Smart Duplicate Detection**: Checks existing job URLs before scraping
- **Recent Jobs Only**: Filters to jobs posted in last 30 days
- **Batch Processing**: Processes jobs in efficient batches
- **Rate Limiting**: Respectful delays between requests

### Database Optimization
- **Auto Cleanup**: Removes jobs older than 60 days
- **Efficient Queries**: Uses indexed lookups for duplicate checking
- **Transaction Batching**: Groups database operations

### Resource Management
- **Memory Limits**: Service limited to 2GB RAM
- **CPU Throttling**: Limited to 80% CPU usage
- **Connection Pooling**: Reuses HTTP connections

## 🔧 Managing the Scheduler

### Service Commands
```bash
# Check status
sudo systemctl status job-scraper

# View live logs
sudo journalctl -u job-scraper -f

# Stop service
sudo systemctl stop job-scraper

# Start service
sudo systemctl start job-scraper

# Restart service
sudo systemctl restart job-scraper

# Disable automatic startup
sudo systemctl disable job-scraper
```

### Manual Operations
```bash
# Run all companies once
python3 scraper/scheduler.py run

# Run specific company
python3 scraper/scheduler.py run Apple
python3 scraper/scheduler.py run NVIDIA

# Test with debug output
python3 scraper/scheduler.py test Apple
```

### Quick Commands
```bash
# Using the setup script for common operations
./setup_scheduler.sh status    # Check service status
./setup_scheduler.sh logs      # View logs
./setup_scheduler.sh stop      # Stop service
./setup_scheduler.sh test      # Test scheduler
```

## 📊 Monitoring and Logs

### Log Locations
- **Service logs**: `sudo journalctl -u job-scraper`
- **Scheduler logs**: `logs/scheduler.log`
- **Scraper logs**: `logs/scraper.log`

### Key Metrics to Monitor
```bash
# View recent scraping activity
sudo journalctl -u job-scraper --since "1 hour ago"

# Check for errors
sudo journalctl -u job-scraper -p err

# Monitor resource usage
sudo systemctl show job-scraper --property=MemoryCurrent,CPUUsageNSec
```

### Sample Log Output
```
2024-06-20 12:00:01 - Starting scheduled scrape
2024-06-20 12:00:01 - Found 194 existing jobs for Apple
2024-06-20 12:00:15 - Scraped 211 jobs from Apple
2024-06-20 12:00:15 - Filtered to 45 recent jobs (last 30 days)
2024-06-20 12:00:16 - Apple scrape complete: 211 scraped, 12 saved, 33 skipped, 0 errors in 15.2s
2024-06-20 12:00:26 - Found 700 existing jobs for NVIDIA
2024-06-20 12:00:45 - Scraped 576 jobs from NVIDIA
2024-06-20 12:00:45 - Filtered to 89 recent jobs (last 30 days)
2024-06-20 12:00:47 - NVIDIA scrape complete: 576 scraped, 8 saved, 81 skipped, 0 errors in 21.3s
2024-06-20 12:00:47 - Scheduled scrape summary: 2 companies, 787 scraped, 20 saved, 114 skipped, 0 errors
```

## 🎯 Performance Optimization

### Typical Performance
- **Apple**: ~211 jobs scraped, ~15 seconds
- **NVIDIA**: ~576 jobs scraped, ~25 seconds
- **Total time**: ~45 seconds per run
- **New jobs saved**: 10-30 per run (incremental)
- **Duplicate skip rate**: 80-90% (very efficient)

### Resource Usage
- **Memory**: ~200-500MB during scraping
- **CPU**: ~20-40% during active scraping
- **Network**: ~5-10MB per run
- **Storage**: ~1-2MB database growth per day

## 🛠️ Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status job-scraper

# View detailed logs
sudo journalctl -u job-scraper -n 50

# Common fixes
sudo systemctl daemon-reload
sudo systemctl restart job-scraper
```

#### Missing Dependencies
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
python3 -m playwright install

# Test manually
python3 scraper/scheduler.py test Apple
```

#### Database Issues
```bash
# Check database permissions
ls -la data/jobs.db

# Recreate database if corrupted
rm data/jobs.db
python3 scraper/scheduler.py test Apple
```

#### Network/Rate Limiting
The scrapers include built-in rate limiting and retry logic:
- **Delays**: 0.5-1 second between requests
- **Retries**: Automatic retry on failures
- **Backoff**: Exponential backoff on rate limits

### Getting Help
```bash
# Test individual components
python3 scraper/scheduler.py test Apple
python3 scraper/main.py Apple

# Check API connectivity
curl http://localhost:8000/companies

# View full system status
./setup_scheduler.sh status
```

## 🔄 Updating the Scheduler

### Adding New Companies
1. Create new scraper in `scraper/` directory
2. Add to `scheduler.py` scrapers dict
3. Restart service: `sudo systemctl restart job-scraper`

### Changing Schedule
Edit the schedule in `scraper/scheduler.py`:
```python
# Current schedule (12 PM and 12 AM)
schedule.every().day.at("12:00").do(self.run_scheduled_scrape)
schedule.every().day.at("00:00").do(self.run_scheduled_scrape)

# Example: Every 6 hours
schedule.every(6).hours.do(self.run_scheduled_scrape)

# Example: Weekdays only at 9 AM
schedule.every().monday.at("09:00").do(self.run_scheduled_scrape)
schedule.every().tuesday.at("09:00").do(self.run_scheduled_scrape)
# ... etc
```

Then restart: `sudo systemctl restart job-scraper`

## 📈 Expected Results

### Daily Scraping Results
- **New jobs found**: 10-50 per day
- **Duplicate jobs skipped**: 200-800 per day
- **Energy savings**: 80-90% vs full scraping
- **Time savings**: 85-95% vs full scraping

### Database Growth
- **Daily growth**: ~1-3MB
- **Monthly growth**: ~30-90MB
- **Auto cleanup**: Keeps last 60 days (~2-6GB max)

---

## 🎉 You're All Set!

The scheduler is now running automatically and will:
- ✅ Scrape jobs twice daily at 12 PM and 12 AM
- ✅ Only process new jobs (energy efficient)
- ✅ Skip duplicates automatically
- ✅ Clean up old data
- ✅ Restart automatically on failures
- ✅ Provide detailed logging

Monitor with: `sudo journalctl -u job-scraper -f` 