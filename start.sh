#!/bin/bash

# IOC Scraper Quick Start Script

echo "🛡️  IOC Scraper - Quick Start"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. You can modify it if needed."
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start the application
echo "🚀 Building and starting the application..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 IOC Scraper is now running!"
    echo ""
    echo "📱 Web Interface: http://localhost"
    echo "🔌 API Backend:   http://localhost:5000"
    echo "🗄️  Database:     localhost:5433"
    echo ""
    echo "📚 Quick Start Guide:"
    echo "1. Open http://localhost in your browser"
    echo "2. Go to 'Sources' to add URLs for periodic scraping"
    echo "3. Use 'Ad-hoc Scrape' for one-time URL analysis"
    echo "4. Browse 'IOCs' to view extracted indicators"
    echo "5. Check 'Sessions' for scraping history"
    echo ""
    echo "📋 To view logs: docker-compose logs -f"
    echo "🛑 To stop:      docker-compose down"
    echo ""
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
fi 