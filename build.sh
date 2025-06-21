#!/bin/bash
set -e

echo "Starting build process..."

# Clear pip cache
pip cache purge || true

# Upgrade pip
pip install --upgrade pip

# Install dependencies with no cache
pip install --no-cache-dir --force-reinstall -r requirements.txt

echo "Build completed successfully!" 