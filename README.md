# IOC Scraper

A comprehensive web application for scraping external URLs and APIs to extract Indicators of Compromise (IOCs). Built with Vue.js frontend, Flask backend, and PostgreSQL database.

## Features

### IOC Types Supported
- **IP Addresses** (IPv4 and IPv6)
- **URLs** (HTTP/HTTPS/FTP)
- **Domain Names**
- **File Hashes** (MD5, SHA1, SHA256, SHA512)
- **Filenames** (with suspicious extensions)
- **ASNs** (Autonomous System Numbers)

### Key Capabilities
- **Source Management**: Maintain a list of URLs for periodic scraping
- **Ad-hoc Scraping**: On-demand scraping of any URL
- **IOC Database**: Persistent storage and search of extracted IOCs
- **Session Tracking**: Track and review scraping activities
- **Confidence Scoring**: AI-based confidence assessment for IOCs
- **Context Preservation**: Store surrounding text for each IOC
- **Modern UI**: Responsive Vue.js interface with Bootstrap styling

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js        │    │   Flask API     │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 80)     │    │   (Port 5000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autoscraper
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000
   - Database: localhost:5433

### Initial Setup

1. The database will be automatically created and initialized
2. Access the web interface at http://localhost
3. Start by adding source URLs in the "Sources" section
4. Perform ad-hoc scrapes or wait for periodic scraping

## Development Setup

### Backend Development

1. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up database**
   ```bash
   # Start PostgreSQL (via Docker or local installation)
   export DATABASE_URL=postgresql://user:password@localhost:5432/iocdb
   python run.py
   ```

### Frontend Development

1. **Set up Node.js environment**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run serve
   ```

3. **Build for production**
   ```bash
   npm run build
   ```

## API Documentation

### Source URLs
- `GET /api/sources` - List all source URLs
- `POST /api/sources` - Create new source URL
- `PUT /api/sources/<id>` - Update source URL
- `DELETE /api/sources/<id>` - Delete source URL

### Scraping
- `POST /api/scrape/adhoc` - Perform ad-hoc scrape
- `POST /api/scrape/source/<id>` - Scrape specific source

### IOCs
- `GET /api/iocs` - List IOCs (with pagination and filtering)
- `GET /api/iocs/stats` - Get IOC statistics

### Sessions
- `GET /api/sessions` - List scrape sessions
- `GET /api/sessions/<id>/iocs` - Get IOCs for specific session

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/iocdb` |
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` |
| `VUE_APP_API_URL` | Backend API URL for frontend | `http://localhost:5000` |

### Database Schema

The application uses PostgreSQL with the following main tables:
- `source_urls` - Configured URLs for periodic scraping
- `scrape_sessions` - Individual scraping activities
- `iocs` - Extracted indicators of compromise

## IOC Extraction Logic

### Pattern Matching
The system uses regex patterns to identify different IOC types:
- **IP Addresses**: IPv4 and IPv6 pattern matching with validation
- **Domains**: Domain name patterns with TLD validation
- **URLs**: HTTP/HTTPS/FTP URL pattern matching
- **Hashes**: Fixed-length hex patterns for MD5, SHA1, SHA256, SHA512
- **Filenames**: Files with suspicious extensions
- **ASNs**: AS number patterns

### Confidence Scoring
Each IOC receives a confidence score (0-1) based on:
- Context analysis (threat-related keywords)
- IOC type characteristics
- Pattern validation results

### Filtering
- Private IP ranges can be optionally excluded
- Common false-positive domains are filtered
- Validation ensures IOCs meet format requirements

## Monitoring and Logging

- Application logs are available in Docker containers
- Database queries and API calls are logged
- Session tracking provides audit trail

## Security Considerations

- Change default passwords in production
- Use environment variables for sensitive configuration
- Consider rate limiting for public deployments
- Regular security updates for dependencies

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL container is running
   - Verify DATABASE_URL environment variable

2. **Frontend not loading**
   - Ensure backend is accessible
   - Check API proxy configuration

3. **No IOCs found**
   - Verify URL is accessible
   - Check content contains expected IOC types

### Logs

```bash
# View application logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# Follow logs in real-time
docker-compose logs -f backend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue in the repository 