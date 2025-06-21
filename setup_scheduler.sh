#!/bin/bash

echo "🕐 Setting up Tech Job Scraper Scheduler"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo "⚠️  This script should not be run as root for security reasons."
        echo "Please run as a regular user. The script will use sudo when needed."
        exit 1
    fi
}

# Function to install Python dependencies
install_dependencies() {
    echo "📦 Installing Python dependencies..."
    pip3 install --user -r requirements.txt
    
    # Install Playwright browsers
    echo "🌐 Installing Playwright browsers..."
    python3 -m playwright install
}

# Function to create systemd service
create_service() {
    echo "🔧 Creating systemd service..."
    
    # Get current user
    CURRENT_USER=$(whoami)
    
    # Create service file with correct paths
    cat > /tmp/job-scraper.service << EOF
[Unit]
Description=Tech Job Scraper Scheduler
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONPATH=$PROJECT_DIR
Environment=HOME=/home/$CURRENT_USER
ExecStart=/usr/bin/python3 $PROJECT_DIR/scraper/scheduler.py start
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=job-scraper

# Resource limits
MemoryMax=2G
CPUQuota=80%

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Copy service file to systemd directory
    sudo cp /tmp/job-scraper.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    echo "✅ Service created successfully"
}

# Function to setup scheduler
setup_scheduler() {
    echo "⚙️  Setting up scheduler configuration..."
    
    # Test the scheduler
    echo "🧪 Testing scheduler..."
    cd "$PROJECT_DIR"
    python3 scraper/scheduler.py test Apple
    
    if [ $? -eq 0 ]; then
        echo "✅ Scheduler test successful"
    else
        echo "❌ Scheduler test failed"
        exit 1
    fi
}

# Function to start service
start_service() {
    echo "🚀 Starting job scraper service..."
    
    sudo systemctl enable job-scraper
    sudo systemctl start job-scraper
    
    # Check status
    sleep 3
    if sudo systemctl is-active --quiet job-scraper; then
        echo "✅ Service started successfully"
        echo "📊 Service status:"
        sudo systemctl status job-scraper --no-pager -l
    else
        echo "❌ Service failed to start"
        echo "📋 Service logs:"
        sudo journalctl -u job-scraper --no-pager -l
        exit 1
    fi
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "🎉 Setup complete! Here's how to manage the scheduler:"
    echo ""
    echo "📊 Check status:          sudo systemctl status job-scraper"
    echo "🔍 View logs:             sudo journalctl -u job-scraper -f"
    echo "🛑 Stop service:          sudo systemctl stop job-scraper"
    echo "🚀 Start service:         sudo systemctl start job-scraper"
    echo "🔄 Restart service:       sudo systemctl restart job-scraper"
    echo "❌ Disable service:       sudo systemctl disable job-scraper"
    echo ""
    echo "📅 Schedule: Runs automatically at 12:00 PM and 12:00 AM daily"
    echo "📁 Logs location: /var/log/syslog (search for 'job-scraper')"
    echo "🗂️  Database: $PROJECT_DIR/data/jobs.db"
    echo ""
    echo "🔧 Manual operations:"
    echo "   python3 scraper/scheduler.py run           # Run all companies once"
    echo "   python3 scraper/scheduler.py run Apple     # Run specific company"
    echo "   python3 scraper/scheduler.py test NVIDIA   # Test specific company"
}

# Main execution
main() {
    check_root
    
    echo "🏠 Project directory: $PROJECT_DIR"
    echo "👤 Running as user: $(whoami)"
    
    # Ask for confirmation
    echo ""
    read -p "Do you want to set up the automated job scraper? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    install_dependencies
    setup_scheduler
    create_service
    start_service
    show_usage
}

# Parse command line arguments
case "${1:-}" in
    "install")
        check_root
        install_dependencies
        ;;
    "service")
        create_service
        ;;
    "start")
        start_service
        ;;
    "test")
        cd "$SCRIPT_DIR"
        python3 scraper/scheduler.py test "${2:-}"
        ;;
    "status")
        sudo systemctl status job-scraper
        ;;
    "logs")
        sudo journalctl -u job-scraper -f
        ;;
    "stop")
        sudo systemctl stop job-scraper
        ;;
    *)
        main
        ;;
esac 