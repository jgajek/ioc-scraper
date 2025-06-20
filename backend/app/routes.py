from flask import Blueprint, request, jsonify
from app import db
from app.models import SourceURL, ScrapeSession, IOC, IOCType
from app.scrapers import WebScraper
from datetime import datetime
from sqlalchemy import desc

api = Blueprint('api', __name__)
scraper = WebScraper()

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

# Source URL endpoints
@api.route('/sources', methods=['GET'])
def get_sources():
    """Get all source URLs"""
    sources = SourceURL.query.all()
    return jsonify([source.to_dict() for source in sources])

@api.route('/sources', methods=['POST'])
def create_source():
    """Create a new source URL"""
    data = request.get_json()
    
    if not data or not data.get('url'):
        return jsonify({'error': 'URL is required'}), 400
    
    # Check if URL already exists
    existing = SourceURL.query.filter_by(url=data['url']).first()
    if existing:
        return jsonify({'error': 'URL already exists'}), 409
    
    source = SourceURL(
        url=data['url'],
        name=data.get('name', ''),
        description=data.get('description', ''),
        active=data.get('active', True),
        scrape_interval=data.get('scrape_interval', 3600)
    )
    
    db.session.add(source)
    db.session.commit()
    
    return jsonify(source.to_dict()), 201

@api.route('/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    """Update a source URL"""
    source = SourceURL.query.get_or_404(source_id)
    data = request.get_json()
    
    if data.get('url'):
        source.url = data['url']
    if 'name' in data:
        source.name = data['name']
    if 'description' in data:
        source.description = data['description']
    if 'active' in data:
        source.active = data['active']
    if 'scrape_interval' in data:
        source.scrape_interval = data['scrape_interval']
    
    source.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(source.to_dict())

@api.route('/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    """Delete a source URL"""
    source = SourceURL.query.get_or_404(source_id)
    db.session.delete(source)
    db.session.commit()
    
    return '', 204

# Scraping endpoints
@api.route('/scrape/adhoc', methods=['POST'])
def adhoc_scrape():
    """Perform an ad-hoc scrape of a URL"""
    data = request.get_json()
    
    if not data or not data.get('url'):
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    include_private_ips = data.get('include_private_ips', False)
    
    # Create a temporary scrape session (allow null source_url_id for ad-hoc)
    session = ScrapeSession(
        status='running'
    )
    db.session.add(session)
    db.session.commit()
    
    try:
        # Perform the scrape
        result = scraper.scrape_url(url, include_private_ips)
        
        if result['success']:
            # Save IOCs to database
            iocs_saved = 0
            for ioc_data in result['iocs']:
                ioc = IOC(
                    scrape_session_id=session.id,
                    ioc_type=ioc_data['type'],
                    value=ioc_data['value'],
                    context=ioc_data['context'],
                    confidence=ioc_data['confidence']
                )
                db.session.add(ioc)
                iocs_saved += 1
            
            session.status = 'completed'
            session.iocs_found = iocs_saved
            session.completed_at = datetime.utcnow()
            
        else:
            session.status = 'failed'
            session.error_message = result['error']
            session.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Return session data with IOCs
        response_data = session.to_dict()
        if result['success']:
            response_data['iocs'] = [ioc.to_dict() for ioc in session.iocs]
        
        return jsonify(response_data)
        
    except Exception as e:
        session.status = 'failed'
        session.error_message = str(e)
        session.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500

@api.route('/scrape/source/<int:source_id>', methods=['POST'])
def scrape_source(source_id):
    """Scrape a specific source URL"""
    source = SourceURL.query.get_or_404(source_id)
    
    # Create scrape session
    session = ScrapeSession(
        source_url_id=source.id,
        status='running'
    )
    db.session.add(session)
    db.session.commit()
    
    try:
        # Perform the scrape
        result = scraper.scrape_url(source.url)
        
        if result['success']:
            # Save IOCs to database
            iocs_saved = 0
            for ioc_data in result['iocs']:
                ioc = IOC(
                    scrape_session_id=session.id,
                    ioc_type=ioc_data['type'],
                    value=ioc_data['value'],
                    context=ioc_data['context'],
                    confidence=ioc_data['confidence']
                )
                db.session.add(ioc)
                iocs_saved += 1
            
            session.status = 'completed'
            session.iocs_found = iocs_saved
            session.completed_at = datetime.utcnow()
            source.last_scraped = datetime.utcnow()
            
        else:
            session.status = 'failed'
            session.error_message = result['error']
            session.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(session.to_dict())
        
    except Exception as e:
        session.status = 'failed'
        session.error_message = str(e)
        session.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500

# IOC endpoints
@api.route('/iocs', methods=['GET'])
def get_iocs():
    """Get IOCs with optional filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    ioc_type = request.args.get('type')
    search = request.args.get('search')
    
    query = IOC.query
    
    if ioc_type:
        try:
            ioc_type_enum = IOCType(ioc_type)
            query = query.filter(IOC.ioc_type == ioc_type_enum)
        except ValueError:
            return jsonify({'error': 'Invalid IOC type'}), 400
    
    if search:
        query = query.filter(IOC.value.ilike(f'%{search}%'))
    
    query = query.order_by(desc(IOC.first_seen))
    
    paginated = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'iocs': [ioc.to_dict() for ioc in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page
    })

@api.route('/iocs/stats', methods=['GET'])
def get_ioc_stats():
    """Get IOC statistics"""
    stats = {}
    
    # Count by type
    for ioc_type in IOCType:
        count = IOC.query.filter(IOC.ioc_type == ioc_type).count()
        stats[ioc_type.value] = count
    
    # Total count
    stats['total'] = IOC.query.count()
    
    # Recent activity (last 24 hours)
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    stats['recent'] = IOC.query.filter(IOC.first_seen >= recent_cutoff).count()
    
    return jsonify(stats)

# Session endpoints
@api.route('/sessions', methods=['GET'])
def get_sessions():
    """Get scrape sessions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = ScrapeSession.query.order_by(desc(ScrapeSession.started_at))
    
    paginated = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'sessions': [session.to_dict() for session in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page
    })

@api.route('/sessions/<int:session_id>/iocs', methods=['GET'])
def get_session_iocs(session_id):
    """Get IOCs for a specific session"""
    session = ScrapeSession.query.get_or_404(session_id)
    iocs = IOC.query.filter_by(scrape_session_id=session_id).all()
    
    return jsonify({
        'session': session.to_dict(),
        'iocs': [ioc.to_dict() for ioc in iocs]
    }) 