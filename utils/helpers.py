"""
ComplianceNavigator Utility Functions
Common helper functions used across the application
"""
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re

def generate_id(prefix: str, content: str) -> str:
    """Generate a unique ID from content"""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}_{content_hash[:12]}"

def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.,;:!?()-]', '', text)
    
    return text

def extract_countries(text: str) -> List[str]:
    """Extract country names from text"""
    countries = [
        'Germany', 'France', 'Netherlands', 'Spain', 'Italy', 'UK', 'United Kingdom',
        'United States', 'USA', 'Canada', 'Australia', 'Japan', 'South Korea',
        'Brazil', 'Mexico', 'India', 'China', 'Singapore', 'Switzerland', 'Sweden',
        'Norway', 'Denmark', 'Belgium', 'Austria', 'Portugal', 'Ireland', 'Finland'
    ]
    
    found_countries = []
    text_lower = text.lower()
    
    for country in countries:
        if country.lower() in text_lower:
            found_countries.append(country)
    
    # Handle EU/Europe
    if any(term in text_lower for term in ['eu', 'europe', 'european']):
        found_countries.extend(['Germany', 'France', 'Netherlands'])
    
    return list(set(found_countries))  # Remove duplicates

def extract_industries(text: str) -> List[str]:
    """Extract industry/sector information from text"""
    industry_keywords = {
        'Healthcare': ['health', 'medical', 'telemedicine', 'doctor', 'patient', 'hospital', 'clinic'],
        'Fintech': ['financial', 'banking', 'payment', 'lending', 'crypto', 'blockchain', 'trading'],
        'E-commerce': ['ecommerce', 'e-commerce', 'retail', 'shopping', 'marketplace', 'selling'],
        'SaaS': ['software', 'saas', 'platform', 'service', 'application', 'tool'],
        'Education': ['education', 'learning', 'training', 'course', 'school', 'university'],
        'Real Estate': ['property', 'real estate', 'housing', 'rental', 'mortgage'],
        'Transportation': ['transport', 'mobility', 'ride', 'delivery', 'logistics', 'shipping'],
        'Energy': ['energy', 'renewable', 'solar', 'wind', 'electricity', 'battery'],
        'Food': ['food', 'restaurant', 'delivery', 'catering', 'nutrition', 'dining'],
        'Entertainment': ['gaming', 'media', 'streaming', 'content', 'entertainment', 'music']
    }
    
    text_lower = text.lower()
    detected_industries = []
    
    for industry, keywords in industry_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_industries.append(industry)
    
    return detected_industries

def format_currency(amount: str) -> str:
    """Format currency amounts consistently"""
    if not amount:
        return "N/A"
    
    # Extract numbers from string
    numbers = re.findall(r'\d+', amount.replace(',', ''))
    if not numbers:
        return amount
    
    try:
        value = int(numbers[0])
        if value >= 1000000:
            return f"${value/1000000:.1f}M"
        elif value >= 1000:
            return f"${value/1000:.0f}K"
        else:
            return f"${value}"
    except:
        return amount

def calculate_business_days(start_date: datetime, days: int) -> datetime:
    """Calculate business days from a start date"""
    current_date = start_date
    days_added = 0
    
    while days_added < days:
        current_date += timedelta(days=1)
        # Skip weekends (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            days_added += 1
    
    return current_date

def parse_deadline(deadline_text: str) -> Optional[str]:
    """Parse deadline text into standardized format"""
    if not deadline_text:
        return None
    
    # Common deadline patterns
    patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', r'\3-\1-\2'),  # MM/DD/YYYY -> YYYY-MM-DD
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', r'\1-\2-\3'),    # YYYY-MM-DD
        (r'in (\d+) days?', lambda m: (datetime.now() + timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')),
        (r'in (\d+) weeks?', lambda m: (datetime.now() + timedelta(weeks=int(m.group(1)))).strftime('%Y-%m-%d')),
        (r'in (\d+) months?', lambda m: (datetime.now() + timedelta(days=int(m.group(1))*30)).strftime('%Y-%m-%d'))
    ]
    
    deadline_lower = deadline_text.lower()
    
    for pattern, replacement in patterns:
        match = re.search(pattern, deadline_lower)
        if match:
            if callable(replacement):
                return replacement(match)
            else:
                return re.sub(pattern, replacement, deadline_lower)
    
    return deadline_text  # Return original if no pattern matches

def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_email_domains(text: str) -> List[str]:
    """Extract email domains from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
    matches = re.findall(email_pattern, text)
    return list(set(matches))

def validate_gemini_response(response: str) -> bool:
    """Validate if Gemini response is meaningful"""
    if not response or len(response.strip()) < 10:
        return False
    
    # Check for error indicators
    error_indicators = [
        'error', 'failed', 'unable to', 'cannot', 'sorry', 
        'i don\'t know', 'no information', 'unavailable'
    ]
    
    response_lower = response.lower()
    if any(indicator in response_lower for indicator in error_indicators):
        return False
    
    return True

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}

def format_list_for_display(items: List[str], max_items: int = 5) -> str:
    """Format list for user-friendly display"""
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return ", ".join(items)
    else:
        displayed = items[:max_items]
        remaining = len(items) - max_items
        return f"{', '.join(displayed)} and {remaining} more"

def calculate_priority_score(severity: str, deadline_days: int = None) -> float:
    """Calculate priority score for action items"""
    severity_scores = {
        'critical': 1.0,
        'high': 0.8,
        'medium': 0.5,
        'low': 0.2
    }
    
    base_score = severity_scores.get(severity.lower(), 0.5)
    
    if deadline_days:
        # Urgent deadlines increase priority
        if deadline_days <= 30:
            base_score += 0.2
        elif deadline_days <= 90:
            base_score += 0.1
    
    return min(base_score, 1.0)

def normalize_country_name(country: str) -> str:
    """Normalize country names for consistency"""
    country_mappings = {
        'usa': 'United States',
        'us': 'United States', 
        'united states of america': 'United States',
        'uk': 'United Kingdom',
        'great britain': 'United Kingdom',
        'deutschland': 'Germany',
        'nederland': 'Netherlands',
        'holland': 'Netherlands'
    }
    
    country_lower = country.lower().strip()
    return country_mappings.get(country_lower, country.title())

def get_regulation_complexity_score(text: str) -> float:
    """Calculate complexity score of regulatory text"""
    if not text:
        return 0.0
    
    complexity_indicators = {
        'high': ['shall', 'must', 'required', 'mandatory', 'compliance', 'penalty', 'fine', 'violation'],
        'medium': ['should', 'recommended', 'advised', 'guideline', 'standard', 'practice'],
        'low': ['may', 'optional', 'voluntary', 'suggested', 'consider']
    }
    
    text_lower = text.lower()
    score = 0.0
    
    for level, indicators in complexity_indicators.items():
        count = sum(1 for indicator in indicators if indicator in text_lower)
        if level == 'high':
            score += count * 0.3
        elif level == 'medium':
            score += count * 0.2
        else:
            score += count * 0.1
    
    return min(score, 1.0) 