import sys
import os

# Add your project directory to the sys.path
sys.path.insert(0, "/home/yourusername/job-scraper")

from api.main import app

# WSGI callable
application = app 