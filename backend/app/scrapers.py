import re
import requests
import ipaddress
from urllib.parse import urlparse
from typing import List, Dict, Set
from bs4 import BeautifulSoup, Comment
from app.models import IOCType

class IOCExtractor:
    def __init__(self):
        # Regex patterns for different IOC types
        self.patterns = {
            IOCType.IP_ADDRESS: [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',  # IPv4
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6 full
                r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:(?:[0-9a-fA-F]{1,4}){0,7}\b'  # IPv6 compressed
            ],
            IOCType.DOMAIN: [
                r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
            ],
            IOCType.URL: [
                r'https?://(?:[-\w.])+(?::[0-9]+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?',
                r'ftp://(?:[-\w.])+(?::[0-9]+)?(?:/[^\s]*)?'
            ],
            IOCType.HASH: [
                r'\b[a-fA-F0-9]{32}\b',  # MD5
                r'\b[a-fA-F0-9]{40}\b',  # SHA1
                r'\b[a-fA-F0-9]{64}\b',  # SHA256
                r'\b[a-fA-F0-9]{128}\b'  # SHA512
            ],
            IOCType.FILENAME: [
                r'\b[\w\-. ]+\.(?:exe|dll|bat|cmd|scr|pif|com|jar|zip|rar|7z|tar|gz|doc|docx|xls|xlsx|pdf|js|vbs|ps1|sh)\b'
            ],
            IOCType.ASN: [
                r'\bAS\d{1,10}\b',
                r'\b(?:ASN|asn)\s*:?\s*\d{1,10}\b'
            ]
        }
        
        # Common false positive domains to filter out
        self.domain_whitelist = {
            # Generic/Example domains
            'example.com', 'localhost', 'example.org', 'example.net', 'test.com',
            
            # Major tech companies (usually false positives)
            'microsoft.com', 'google.com', 'github.com', 'stackoverflow.com',
            'apple.com', 'amazon.com', 'aws.amazon.com', 'cloudfront.net',
            'azurewebsites.net', 'azure.com', 'office.com', 'live.com',
            'outlook.com', 'hotmail.com', 'gmail.com', 'yahoo.com',
            
            # CDNs and common infrastructure
            'cloudflare.com', 'fastly.com', 'akamai.com', 'jquery.com',
            'cdnjs.cloudflare.com', 'bootstrapcdn.com', 'maxcdn.bootstrapcdn.com',
            'fonts.googleapis.com', 'fonts.gstatic.com', 'ajax.googleapis.com',
            'code.jquery.com', 'unpkg.com', 'jsdelivr.net',
            
            # Social media (usually references, not threats)
            'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com',
            'instagram.com', 'tiktok.com', 'reddit.com',
            
            # Certificate authorities and security vendors
            'digicert.com', 'letsencrypt.org', 'sectigo.com', 'globalsign.com',
            'symantec.com', 'verisign.com', 'godaddy.com',
            
            # Common file extensions that aren't threats when from legitimate sites
            'w3.org', 'mozilla.org', 'ietf.org', 'rfc-editor.org'
        }
        
        # Private IP ranges to potentially filter
        self.private_ip_ranges = [
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16'),
            ipaddress.ip_network('127.0.0.0/8')
        ]

    def extract_iocs(self, text: str, include_private_ips: bool = False) -> List[Dict]:
        """Extract all IOCs from text"""
        iocs = []
        
        for ioc_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group().strip()
                    context = self._get_context(text, match.start(), match.end())
                    
                    # Validation and filtering
                    if self._validate_ioc(ioc_type, value, include_private_ips):
                        iocs.append({
                            'type': ioc_type,
                            'value': value,
                            'context': context,
                            'confidence': self._calculate_confidence(ioc_type, value, context)
                        })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_iocs = []
        for ioc in iocs:
            key = (ioc['type'], ioc['value'])
            if key not in seen:
                seen.add(key)
                unique_iocs.append(ioc)
        
        return unique_iocs

    def _get_context(self, text: str, start: int, end: int, context_size: int = 100) -> str:
        """Get surrounding context for an IOC"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()

    def _validate_ioc(self, ioc_type: IOCType, value: str, include_private_ips: bool) -> bool:
        """Validate and filter IOCs"""
        try:
            if ioc_type == IOCType.IP_ADDRESS:
                ip = ipaddress.ip_address(value)
                # Filter out private IPs if not requested
                if not include_private_ips:
                    for private_range in self.private_ip_ranges:
                        if ip in private_range:
                            return False
                return True
                
            elif ioc_type == IOCType.DOMAIN:
                value_lower = value.lower()
                
                # Check against whitelist (exact match and subdomain match)
                if value_lower in self.domain_whitelist:
                    return False
                
                # Check if it's a subdomain of whitelisted domains
                for whitelisted in self.domain_whitelist:
                    if value_lower.endswith('.' + whitelisted):
                        return False
                
                # Must have at least one dot and valid TLD
                if '.' not in value or len(value.split('.')[-1]) < 2:
                    return False
                
                # Filter out common CDN patterns
                cdn_patterns = [
                    'static.', 'assets.', 'cdn.', 'img.', 'images.', 'media.',
                    'css.', 'js.', 'fonts.', 'api.', 'www.gstatic.com'
                ]
                if any(value_lower.startswith(pattern) for pattern in cdn_patterns):
                    return False
                
                return True
                
            elif ioc_type == IOCType.URL:
                parsed = urlparse(value)
                if not (parsed.scheme and parsed.netloc):
                    return False
                
                # Apply domain filtering to URL hosts
                host = parsed.netloc.lower()
                
                # Remove port if present
                if ':' in host:
                    host = host.split(':')[0]
                
                # Check against domain whitelist for URLs too
                if host in self.domain_whitelist:
                    return False
                
                # Check if it's a subdomain of whitelisted domains
                for whitelisted in self.domain_whitelist:
                    if host.endswith('.' + whitelisted):
                        return False
                
                return True
                
            elif ioc_type == IOCType.HASH:
                # Must be hex and correct length
                return bool(re.match(r'^[a-fA-F0-9]+$', value))
                
            elif ioc_type == IOCType.FILENAME:
                # Basic filename validation
                if not (len(value) > 0 and '.' in value):
                    return False
                
                # Filter out very common/generic filenames
                generic_files = {
                    'index.html', 'index.htm', 'main.js', 'app.js', 'jquery.js',
                    'bootstrap.css', 'style.css', 'main.css', 'app.css',
                    'favicon.ico', 'robots.txt', 'sitemap.xml', 'manifest.json'
                }
                
                if value.lower() in generic_files:
                    return False
                
                return True
                
            elif ioc_type == IOCType.ASN:
                # Extract number from ASN
                asn_match = re.search(r'\d+', value)
                if asn_match:
                    asn_num = int(asn_match.group())
                    return 1 <= asn_num <= 4294967295  # Valid ASN range
                return False
                
        except Exception:
            return False
        
        return True

    def _calculate_confidence(self, ioc_type: IOCType, value: str, context: str) -> float:
        """Calculate confidence score for IOC"""
        confidence = 0.6  # Higher base confidence since we're analyzing visible content only
        
        # Increase confidence based on context keywords
        threat_keywords = [
            'malware', 'threat', 'malicious', 'suspicious', 'infected', 'virus',
            'trojan', 'backdoor', 'c2', 'command', 'control', 'botnet', 'phishing',
            'attack', 'exploit', 'vulnerability', 'breach', 'compromise', 'incident',
            'indicator', 'ioc', 'artifact', 'campaign', 'apt', 'actor'
        ]
        
        context_lower = context.lower()
        threat_score = sum(1 for keyword in threat_keywords if keyword in context_lower)
        confidence += min(0.3, threat_score * 0.05)  # Up to 0.3 bonus for threat context
        
        # Type-specific confidence adjustments
        if ioc_type == IOCType.HASH:
            if len(value) == 64:  # SHA256 is more commonly used for malware
                confidence += 0.15
            elif len(value) == 32:  # MD5
                confidence += 0.1
        elif ioc_type == IOCType.FILENAME:
            suspicious_extensions = ['.exe', '.scr', '.bat', '.cmd', '.pif', '.com', '.dll']
            if any(value.lower().endswith(ext) for ext in suspicious_extensions):
                confidence += 0.2
        elif ioc_type == IOCType.IP_ADDRESS:
            # Non-RFC1918 IPs in visible content are more suspicious
            try:
                ip = ipaddress.ip_address(value)
                if not any(ip in network for network in self.private_ip_ranges):
                    confidence += 0.1
            except:
                pass
        elif ioc_type == IOCType.URL:
            # URLs with suspicious patterns
            suspicious_url_patterns = ['bit.ly', 'tinyurl', 'shortened', 'redirect']
            if any(pattern in value.lower() for pattern in suspicious_url_patterns):
                confidence += 0.1
        
        return min(1.0, confidence)

class WebScraper:
    def __init__(self):
        self.extractor = IOCExtractor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_visible_text(self, html_content: str) -> str:
        """Extract only user-visible text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Remove hidden elements (common hidden element selectors)
            hidden_selectors = [
                '[style*="display:none"]',
                '[style*="display: none"]',
                '[style*="visibility:hidden"]',
                '[style*="visibility: hidden"]',
                '.hidden',
                '.sr-only',  # Screen reader only
                '.visually-hidden',
                '[aria-hidden="true"]',
                '[hidden]'
            ]
            
            for selector in hidden_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Remove common non-content elements
            non_content_tags = ['head', 'meta', 'link', 'title']
            for tag in non_content_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Get text from remaining elements, focusing on content areas
            visible_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            visible_text = ' '.join(visible_text.split())
            
            return visible_text
            
        except Exception as e:
            # Fallback to raw content if HTML parsing fails
            print(f"HTML parsing failed: {e}. Using raw content.")
            return html_content

    def scrape_url(self, url: str, include_private_ips: bool = False) -> Dict:
        """Scrape a URL and extract IOCs from visible content only"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Get raw HTML content
            raw_content = response.text
            
            # Determine content type
            content_type = response.headers.get('content-type', '').lower()
            
            if 'html' in content_type:
                # Extract only visible text from HTML
                visible_content = self.extract_visible_text(raw_content)
                content_to_analyze = visible_content
                content_type_used = 'html_visible'
            else:
                # For non-HTML content (plain text, JSON, XML, etc.), use as-is
                content_to_analyze = raw_content
                content_type_used = 'raw'
            
            # Extract IOCs from the processed content
            iocs = self.extractor.extract_iocs(content_to_analyze, include_private_ips)
            
            return {
                'success': True,
                'iocs': iocs,
                'content_length': len(raw_content),
                'visible_content_length': len(content_to_analyze),
                'content_type': content_type_used,
                'status_code': response.status_code
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'iocs': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'iocs': []
            } 