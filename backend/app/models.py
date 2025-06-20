from app import db
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class IOCType(Enum):
    IP_ADDRESS = "ip_address"
    URL = "url"
    DOMAIN = "domain"
    HASH = "hash"
    FILENAME = "filename"
    ASN = "asn"

class SourceURL(db.Model):
    __tablename__ = 'source_urls'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    scrape_interval = db.Column(db.Integer, default=3600)  # seconds
    last_scraped = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scrape_sessions = db.relationship('ScrapeSession', backref='source_url', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'description': self.description,
            'active': self.active,
            'scrape_interval': self.scrape_interval,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ScrapeSession(db.Model):
    __tablename__ = 'scrape_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    source_url_id = db.Column(db.Integer, db.ForeignKey('source_urls.id'), nullable=True)  # Allow null for ad-hoc scrapes
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    iocs_found = db.Column(db.Integer, default=0)
    
    # Relationships
    iocs = db.relationship('IOC', backref='scrape_session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_url_id': self.source_url_id,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'iocs_found': self.iocs_found
        }

class IOC(db.Model):
    __tablename__ = 'iocs'
    
    id = db.Column(db.Integer, primary_key=True)
    scrape_session_id = db.Column(db.Integer, db.ForeignKey('scrape_sessions.id'), nullable=False)
    ioc_type = db.Column(SQLEnum(IOCType), nullable=False)
    value = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)  # surrounding text where IOC was found
    confidence = db.Column(db.Float, default=1.0)  # confidence score 0-1
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scrape_session_id': self.scrape_session_id,
            'ioc_type': self.ioc_type.value,
            'value': self.value,
            'context': self.context,
            'confidence': self.confidence,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        } 