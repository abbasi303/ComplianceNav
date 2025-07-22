"""
AI-Powered Link Validation Agent
Uses cutting-edge AI techniques to validate and verify regulatory links
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
from loguru import logger
import hashlib
import time
from datetime import datetime, timedelta

from integrations.gemini_client import gemini_client
from agents.scout_agent import RegulatoryDocument


@dataclass
class ValidationResult:
    """Result from link validation"""
    url: str
    is_valid: bool
    is_regulatory: bool
    authority_verified: bool
    content_freshness: float
    accessibility_score: float
    regulatory_relevance: float
    validation_confidence: float
    issues: List[str]
    recommendations: List[str]


class LinkValidationAgent:
    """
    Advanced AI-powered link validation using cutting-edge techniques:
    - Multi-dimensional validation
    - AI content analysis
    - Authority verification
    - Freshness assessment
    - Accessibility testing
    - Regulatory relevance scoring
    """
    
    def __init__(self):
        self.agent_name = "LinkValidationAgent"
        self.session_pool = None
        self.validation_cache = {}
        self.authority_database = self._load_authority_database()
        
        # Validation settings
        self.timeout = 30
        self.max_redirects = 5
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        logger.info(f"{self.agent_name} initialized with advanced validation capabilities")
    
    def _load_authority_database(self) -> Dict[str, Dict]:
        """Load database of known regulatory authorities"""
        return {
            "EU": {
                "eur-lex.europa.eu": {"name": "EUR-Lex", "credibility": 0.95},
                "europa.eu": {"name": "European Commission", "credibility": 0.95},
                "ec.europa.eu": {"name": "European Commission", "credibility": 0.95}
            },
            "Germany": {
                "gesetze-im-internet.de": {"name": "German Federal Laws", "credibility": 0.95},
                "bafin.de": {"name": "BaFin", "credibility": 0.95},
                "bundesbank.de": {"name": "Deutsche Bundesbank", "credibility": 0.95},
                "bsi.bund.de": {"name": "BSI", "credibility": 0.95}
            },
            "Pakistan": {
                "secp.gov.pk": {"name": "SECP", "credibility": 0.90},
                "fbr.gov.pk": {"name": "FBR", "credibility": 0.90},
                "pta.gov.pk": {"name": "PTA", "credibility": 0.90},
                "sbp.org.pk": {"name": "State Bank of Pakistan", "credibility": 0.90},
                "psqca.gov.pk": {"name": "PSQCA", "credibility": 0.90}
            },
            "US": {
                "federalregister.gov": {"name": "Federal Register", "credibility": 0.95},
                "sec.gov": {"name": "SEC", "credibility": 0.95},
                "federalreserve.gov": {"name": "Federal Reserve", "credibility": 0.95},
                "ftc.gov": {"name": "FTC", "credibility": 0.95}
            }
        }
    
    async def validate_regulatory_links(
        self, 
        documents: List[RegulatoryDocument]
    ) -> List[RegulatoryDocument]:
        """
        Validate regulatory links using advanced AI techniques
        """
        logger.info(f"{self.agent_name}: Validating {len(documents)} regulatory links")
        
        # Initialize session pool
        self.session_pool = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': self.user_agents[0]}
        )
        
        try:
            validated_docs = []
            
            # Process documents in parallel batches
            batch_size = 5
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Validate batch in parallel
                batch_tasks = [self._validate_single_document(doc) for doc in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, RegulatoryDocument):
                        validated_docs.append(result)
                
                # Rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"{self.agent_name}: Validated {len(validated_docs)} documents")
            return validated_docs
            
        finally:
            if self.session_pool:
                await self.session_pool.close()
    
    async def _validate_single_document(self, doc: RegulatoryDocument) -> Optional[RegulatoryDocument]:
        """Validate a single regulatory document"""
        
        if not doc.url:
            return doc  # No URL to validate
        
        try:
            # Check cache first
            cache_key = hashlib.md5(doc.url.encode()).hexdigest()
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                if time.time() - cached_result.get('timestamp', 0) < 3600:  # 1 hour cache
                    return self._apply_validation_result(doc, cached_result['result'])
            
            # Perform comprehensive validation
            validation_result = await self._comprehensive_validation(doc.url, doc.country)
            
            # Cache result
            self.validation_cache[cache_key] = {
                'result': validation_result,
                'timestamp': time.time()
            }
            
            # Apply validation results
            return self._apply_validation_result(doc, validation_result)
            
        except Exception as e:
            logger.error(f"Error validating document {doc.url}: {e}")
            return doc  # Return original document on error
    
    async def _comprehensive_validation(self, url: str, country: str) -> ValidationResult:
        """Perform comprehensive validation of a URL"""
        
        validation_result = ValidationResult(
            url=url,
            is_valid=False,
            is_regulatory=False,
            authority_verified=False,
            content_freshness=0.0,
            accessibility_score=0.0,
            regulatory_relevance=0.0,
            validation_confidence=0.0,
            issues=[],
            recommendations=[]
        )
        
        try:
            # Step 1: Basic URL validation
            if not self._validate_url_format(url):
                validation_result.issues.append("Invalid URL format")
                return validation_result
            
            # Step 2: Accessibility testing
            accessibility_result = await self._test_accessibility(url)
            validation_result.accessibility_score = accessibility_result['score']
            validation_result.issues.extend(accessibility_result['issues'])
            
            if not accessibility_result['accessible']:
                return validation_result
            
            # Step 3: Authority verification
            authority_result = await self._verify_authority(url, country)
            validation_result.authority_verified = authority_result['verified']
            validation_result.issues.extend(authority_result['issues'])
            
            # Step 4: Content analysis
            content_result = await self._analyze_content(url, country)
            validation_result.is_regulatory = content_result['is_regulatory']
            validation_result.regulatory_relevance = content_result['relevance']
            validation_result.content_freshness = content_result['freshness']
            validation_result.issues.extend(content_result['issues'])
            
            # Step 5: AI-powered validation
            ai_result = await self._ai_validation(url, content_result['content'])
            validation_result.validation_confidence = ai_result['confidence']
            validation_result.recommendations.extend(ai_result['recommendations'])
            
            # Step 6: Calculate overall validity
            validation_result.is_valid = self._calculate_overall_validity(validation_result)
            
            return validation_result
            
        except Exception as e:
            validation_result.issues.append(f"Validation error: {str(e)}")
            return validation_result
    
    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def _test_accessibility(self, url: str) -> Dict:
        """Test URL accessibility"""
        result = {
            'accessible': False,
            'score': 0.0,
            'issues': []
        }
        
        try:
            async with self.session_pool.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    result['accessible'] = True
                    result['score'] = 1.0
                    
                    # Check for common issues
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' not in content_type:
                        result['issues'].append("Non-HTML content")
                        result['score'] = 0.5
                    
                    # Check response time
                    if response.headers.get('x-response-time'):
                        response_time = float(response.headers['x-response-time'])
                        if response_time > 5.0:
                            result['issues'].append("Slow response time")
                            result['score'] *= 0.8
                    
                else:
                    result['issues'].append(f"HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            result['issues'].append("Timeout")
        except Exception as e:
            result['issues'].append(f"Accessibility error: {str(e)}")
        
        return result
    
    async def _verify_authority(self, url: str, country: str) -> Dict:
        """Verify if URL belongs to a known regulatory authority"""
        result = {
            'verified': False,
            'issues': []
        }
        
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check against authority database
            for region, authorities in self.authority_database.items():
                if domain in authorities:
                    result['verified'] = True
                    return result
            
            # Check for government domain patterns
            gov_patterns = ['.gov.', '.gouv.', '.govt.']
            if any(pattern in domain for pattern in gov_patterns):
                result['verified'] = True
                return result
            
            # Check for regulatory keywords in domain
            regulatory_keywords = ['regulation', 'regulator', 'authority', 'commission', 'ministry']
            if any(keyword in domain for keyword in regulatory_keywords):
                result['verified'] = True
                return result
            
            result['issues'].append("Unknown authority domain")
            
        except Exception as e:
            result['issues'].append(f"Authority verification error: {str(e)}")
        
        return result
    
    async def _analyze_content(self, url: str, country: str) -> Dict:
        """Analyze content for regulatory relevance"""
        
        result = {
            'content': '',
            'relevance': 0.0,
            'is_regulatory': False,
            'freshness': 0.5,
            'issues': []
        }
        
        try:
            # Create a new session to avoid loop issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract main content
                        main_content = self._extract_main_content(soup)
                        result['content'] = main_content
                        
                        # Check for regulatory keywords
                        regulatory_keywords = [
                            'regulation', 'compliance', 'licensing', 'permit',
                            'registration', 'data protection', 'privacy',
                            'financial services', 'banking', 'securities'
                        ]
                        
                        content_lower = main_content.lower()
                        keyword_matches = sum(1 for keyword in regulatory_keywords 
                                            if keyword in content_lower)
                        
                        result['relevance'] = min(keyword_matches * 0.2, 1.0)
                        result['is_regulatory'] = result['relevance'] > 0.3
                        
                        # Check content freshness
                        result['freshness'] = self._assess_content_freshness(soup, response.headers)
                        
                    else:
                        result['issues'].append(f"Content analysis failed: HTTP {response.status}")
                        
        except Exception as e:
            result['issues'].append(f"Content analysis error: {str(e)}")
        
        return result
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '.main-content', 
            '#content', '#main', '.body', '.text'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Fallback to body text
        return soup.get_text().strip()
    
    def _assess_content_freshness(self, soup: BeautifulSoup, headers: Dict) -> float:
        """Assess content freshness"""
        freshness_score = 0.5  # Base score
        
        # Check last-modified header
        last_modified = headers.get('last-modified')
        if last_modified:
            try:
                last_modified_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                days_old = (datetime.now() - last_modified_date).days
                
                if days_old < 30:
                    freshness_score += 0.3
                elif days_old < 365:
                    freshness_score += 0.1
                else:
                    freshness_score -= 0.2
                    
            except:
                pass
        
        # Check for date patterns in content
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}'
        ]
        
        content_text = soup.get_text()
        for pattern in date_patterns:
            dates = re.findall(pattern, content_text)
            if dates:
                freshness_score += 0.1
                break
        
        return min(freshness_score, 1.0)
    
    async def _ai_validation(self, url: str, content: str) -> Dict:
        """Use AI to validate regulatory content"""
        result = {
            'confidence': 0.0,
            'recommendations': []
        }
        
        try:
            prompt = f"""
            Analyze this regulatory content for validity and quality:
            
            URL: {url}
            Content: {content[:2000]}...
            
            Assess:
            1. Is this genuine regulatory content?
            2. Is the information current and accurate?
            3. What is the confidence level (0-1)?
            4. Any recommendations for improvement?
            
            Return JSON:
            {{
                "confidence": 0.0-1.0,
                "is_genuine": true/false,
                "is_current": true/false,
                "recommendations": ["rec1", "rec2"]
            }}
            """
            
            ai_response = await gemini_client.generate_response(prompt, temperature=0.2)
            
            # Parse AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_analysis = json.loads(json_match.group())
                result['confidence'] = ai_analysis.get('confidence', 0.0)
                result['recommendations'] = ai_analysis.get('recommendations', [])
            
        except Exception as e:
            logger.error(f"AI validation error: {e}")
        
        return result
    
    def _calculate_overall_validity(self, validation_result: ValidationResult) -> bool:
        """Calculate overall validity based on all validation factors"""
        
        # Weighted scoring
        scores = {
            'accessibility': validation_result.accessibility_score * 0.2,
            'authority': 1.0 if validation_result.authority_verified else 0.0 * 0.3,
            'regulatory': validation_result.regulatory_relevance * 0.3,
            'freshness': validation_result.content_freshness * 0.1,
            'ai_confidence': validation_result.validation_confidence * 0.1
        }
        
        total_score = sum(scores.values())
        
        # Consider valid if score > 0.6 and no critical issues
        critical_issues = ['Invalid URL format', 'Timeout', 'HTTP 404', 'HTTP 500']
        has_critical_issues = any(issue in validation_result.issues for issue in critical_issues)
        
        return total_score > 0.6 and not has_critical_issues
    
    def _apply_validation_result(self, doc: RegulatoryDocument, validation_result: ValidationResult) -> RegulatoryDocument:
        """Apply validation results to document"""
        
        # Adjust relevance score based on validation
        if validation_result.is_valid:
            doc.relevance_score *= validation_result.validation_confidence
        
        # Add validation metadata
        if not hasattr(doc, 'validation_metadata') or doc.validation_metadata is None:
            doc.validation_metadata = {}
        
        doc.validation_metadata.update({
            'validated_at': datetime.now().isoformat(),
            'is_valid': validation_result.is_valid,
            'authority_verified': validation_result.authority_verified,
            'accessibility_score': validation_result.accessibility_score,
            'content_freshness': validation_result.content_freshness,
            'validation_confidence': validation_result.validation_confidence,
            'issues': validation_result.issues,
            'recommendations': validation_result.recommendations
        })
        
        return doc


# Global instance
link_validation_agent = LinkValidationAgent() 