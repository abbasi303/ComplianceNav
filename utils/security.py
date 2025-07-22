"""
Production Security Layer for ComplianceNavigator
Input validation, sanitization, and security middleware
"""
import re
import html
import bleach
import hashlib
import secrets
import json
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
from loguru import logger
from datetime import datetime, timedelta
import base64

class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass

class InputValidationError(SecurityError):
    """Exception raised for invalid input"""
    pass

class SecurityValidator:
    """Comprehensive input validation and sanitization"""
    
    # Dangerous patterns to detect
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',           # XSS scripts
        r'javascript:',                         # JavaScript protocols
        r'on\w+\s*=',                          # Event handlers
        r'eval\s*\(',                          # Code evaluation
        r'exec\s*\(',                          # Code execution
        r'\b(union|select|insert|update|delete|drop)\b',  # SQL injection
        r'\.\./',                              # Path traversal
        r'%2e%2e%2f',                          # Encoded path traversal
        r'<iframe[^>]*>.*?</iframe>',          # Iframe injections
    ]
    
    # Allowed HTML tags for rich text (very restrictive)
    ALLOWED_HTML_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li'
    ]
    
    ALLOWED_HTML_ATTRIBUTES = {
        '*': ['class'],
    }
    
    def __init__(self):
        self.max_input_length = 50000  # Maximum input length
        self.max_url_length = 2048     # Maximum URL length
        self.blocked_domains = ['localhost', '127.0.0.1', '0.0.0.0']  # Block internal access
    
    def validate_user_input(self, input_text: str, context: str = "general") -> str:
        """Validate and sanitize user input"""
        if not isinstance(input_text, str):
            raise InputValidationError(f"Input must be string, got {type(input_text)}")
        
        # Length validation
        if len(input_text) > self.max_input_length:
            raise InputValidationError(f"Input too long: {len(input_text)} > {self.max_input_length}")
        
        if len(input_text.strip()) == 0:
            raise InputValidationError("Input cannot be empty")
        
        # Check for suspicious patterns
        self._check_suspicious_patterns(input_text, context)
        
        # Sanitize based on context
        if context == "html":
            return self._sanitize_html(input_text)
        elif context == "url":
            return self._validate_url(input_text)
        elif context == "json":
            return self._validate_json(input_text)
        else:
            return self._sanitize_general_input(input_text)
    
    def _check_suspicious_patterns(self, text: str, context: str):
        """Check for suspicious patterns in input"""
        text_lower = text.lower()
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Suspicious pattern detected in {context}: {pattern[:50]}")
                raise InputValidationError(f"Suspicious content detected")
    
    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content"""
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            html_content,
            tags=self.ALLOWED_HTML_TAGS,
            attributes=self.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        
        # Additional escape for safety
        return html.escape(cleaned, quote=False)
    
    def _sanitize_general_input(self, text: str) -> str:
        """Sanitize general text input"""
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # HTML escape for safety
        return html.escape(text, quote=False)
    
    def _validate_url(self, url: str) -> str:
        """Validate and sanitize URL"""
        if len(url) > self.max_url_length:
            raise InputValidationError(f"URL too long: {len(url)} > {self.max_url_length}")
        
        try:
            parsed = urlparse(url)
        except Exception:
            raise InputValidationError("Invalid URL format")
        
        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise InputValidationError("Only HTTP/HTTPS URLs allowed")
        
        # Check for blocked domains
        if parsed.hostname:
            hostname_lower = parsed.hostname.lower()
            if any(blocked in hostname_lower for blocked in self.blocked_domains):
                raise InputValidationError("Access to internal resources not allowed")
        
        return url
    
    def _validate_json(self, json_str: str) -> str:
        """Validate JSON input"""
        try:
            # Parse to validate structure
            parsed = json.loads(json_str)
            
            # Check for excessive nesting (JSON bomb protection)
            if self._check_json_depth(parsed) > 10:
                raise InputValidationError("JSON nesting too deep")
            
            # Re-serialize to normalize
            return json.dumps(parsed, separators=(',', ':'))
            
        except json.JSONDecodeError as e:
            raise InputValidationError(f"Invalid JSON: {e}")
    
    def _check_json_depth(self, obj: Any, depth: int = 0) -> int:
        """Check maximum depth of JSON object"""
        if depth > 10:  # Early termination
            return depth
        
        if isinstance(obj, dict):
            return max(self._check_json_depth(v, depth + 1) for v in obj.values()) if obj else depth
        elif isinstance(obj, list):
            return max(self._check_json_depth(item, depth + 1) for item in obj) if obj else depth
        else:
            return depth
    
    def validate_startup_description(self, description: str) -> str:
        """Specialized validation for startup descriptions"""
        # Check minimum meaningful length
        if len(description.strip()) < 10:
            raise InputValidationError("Startup description too short (minimum 10 characters)")
        
        # Check for reasonable maximum
        if len(description) > 5000:
            raise InputValidationError("Startup description too long (maximum 5000 characters)")
        
        # Sanitize and validate
        return self.validate_user_input(description, "general")

class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self):
        self.validator = SecurityValidator()
        self.request_history = {}  # Simple in-memory tracking
        self.blocked_ips = set()
        
    async def validate_request(self, request_data: Dict[str, Any], client_ip: str = None) -> Dict[str, Any]:
        """Validate incoming request"""
        
        # Check for blocked IPs
        if client_ip and client_ip in self.blocked_ips:
            raise SecurityError(f"IP {client_ip} is blocked")
        
        # Track request frequency (simple DoS protection)
        if client_ip:
            await self._track_request_frequency(client_ip)
        
        # Validate request structure
        validated_data = {}
        
        for key, value in request_data.items():
            if key == 'user_query':
                validated_data[key] = self.validator.validate_startup_description(str(value))
            elif key == 'custom_sources' and value:
                validated_data[key] = await self._validate_custom_sources(value)
            elif isinstance(value, str):
                validated_data[key] = self.validator.validate_user_input(value)
            else:
                validated_data[key] = value
        
        return validated_data
    
    async def _track_request_frequency(self, client_ip: str):
        """Track request frequency for DoS protection"""
        now = datetime.now()
        
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Clean old requests (older than 1 minute)
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if now - req_time < timedelta(minutes=1)
        ]
        
        # Add current request
        self.request_history[client_ip].append(now)
        
        # Check if too many requests
        if len(self.request_history[client_ip]) > 30:  # 30 requests per minute max
            logger.warning(f"High request frequency from {client_ip}")
            self.blocked_ips.add(client_ip)
            raise SecurityError("Too many requests. IP temporarily blocked.")
    
    async def _validate_custom_sources(self, custom_sources: List[Dict]) -> List[Dict]:
        """Validate custom sources input"""
        if not isinstance(custom_sources, list):
            raise InputValidationError("Custom sources must be a list")
        
        if len(custom_sources) > 10:  # Limit number of custom sources
            raise InputValidationError("Maximum 10 custom sources allowed")
        
        validated_sources = []
        
        for i, source in enumerate(custom_sources):
            if not isinstance(source, dict):
                raise InputValidationError(f"Custom source {i} must be an object")
            
            validated_source = {}
            
            # Validate source type
            if 'type' not in source:
                raise InputValidationError(f"Custom source {i} missing type")
            
            source_type = str(source['type']).lower()
            if source_type not in ['url', 'text', 'file']:
                raise InputValidationError(f"Invalid custom source type: {source_type}")
            
            validated_source['type'] = source_type
            
            # Validate based on type
            if source_type == 'url':
                if 'url' not in source:
                    raise InputValidationError(f"URL custom source {i} missing url field")
                validated_source['url'] = self.validator.validate_user_input(
                    source['url'], context="url"
                )
            
            elif source_type == 'text':
                if 'content' not in source:
                    raise InputValidationError(f"Text custom source {i} missing content field")
                if len(str(source['content'])) > 50000:  # 50KB limit
                    raise InputValidationError(f"Text custom source {i} content too large")
                validated_source['content'] = self.validator.validate_user_input(
                    str(source['content']), context="general"
                )
            
            elif source_type == 'file':
                if 'content' not in source:
                    raise InputValidationError(f"File custom source {i} missing content field")
                # For file content, we allow bytes or strings
                file_content = source['content']
                if isinstance(file_content, bytes):
                    if len(file_content) > 5 * 1024 * 1024:  # 5MB limit for files
                        raise InputValidationError(f"File custom source {i} content too large (max 5MB)")
                    validated_source['content'] = file_content  # Keep as bytes
                elif isinstance(file_content, str):
                    if len(file_content) > 50000:  # 50KB limit for text files
                        raise InputValidationError(f"File custom source {i} content too large")
                    validated_source['content'] = self.validator.validate_user_input(
                        file_content, context="general"
                    )
                else:
                    raise InputValidationError(f"File custom source {i} content must be bytes or string")
            
            # Validate optional fields
            if 'title' in source:
                validated_source['title'] = self.validator.validate_user_input(
                    str(source['title'])[:200]  # Limit title length
                )
            
            if 'description' in source:
                validated_source['description'] = self.validator.validate_user_input(
                    str(source['description'])[:500]  # Limit description length
                )
            
            validated_sources.append(validated_source)
        
        return validated_sources

class DataEncryption:
    """Simple encryption utilities for sensitive data"""
    
    def __init__(self, key: Optional[bytes] = None):
        if key:
            self.key = key
        else:
            # Generate a random key (should be stored securely in production)
            self.key = secrets.token_bytes(32)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data (simple implementation)"""
        # In production, use proper encryption like Fernet
        try:
            from cryptography.fernet import Fernet
            
            # Use first 32 bytes of key for Fernet (base64 encoded)
            fernet_key = base64.urlsafe_b64encode(self.key[:32])
            f = Fernet(fernet_key)
            
            encrypted_data = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except ImportError:
            # Fallback to simple base64 encoding (NOT SECURE - for demo only)
            logger.warning("Cryptography library not available, using base64 encoding")
            return base64.urlsafe_b64encode(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            from cryptography.fernet import Fernet
            
            fernet_key = base64.urlsafe_b64encode(self.key[:32])
            f = Fernet(fernet_key)
            
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data)
            return decrypted_data.decode()
            
        except ImportError:
            # Fallback base64 decoding
            return base64.urlsafe_b64decode(encrypted_data.encode()).decode()

class SecurityAuditor:
    """Security audit and monitoring"""
    
    def __init__(self):
        self.security_events = []
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], client_ip: str = None):
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details,
            'client_ip': client_ip
        }
        
        self.security_events.append(event)
        
        # Log to file
        logger.warning(f"SECURITY EVENT [{event_type}]: {details}")
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get security report for recent events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > cutoff_time
        ]
        
        # Aggregate by type
        event_counts = {}
        for event in recent_events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(recent_events),
            'event_types': event_counts,
            'recent_events': recent_events[-10:],  # Last 10 events
            'report_period_hours': hours
        }

# Global security instances
security_validator = SecurityValidator()
security_middleware = SecurityMiddleware()  
security_auditor = SecurityAuditor()
data_encryptor = DataEncryption() 