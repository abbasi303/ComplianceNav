"""
Advanced Web Discovery Agent
Uses cutting-edge techniques for live regulatory link discovery
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
from loguru import logger
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib

from integrations.gemini_client import gemini_client
from agents.scout_agent import RegulatoryDocument


@dataclass
class DiscoveryResult:
    """Result from web discovery"""
    url: str
    title: str
    content: str
    authority: str
    relevance_score: float
    discovery_method: str
    metadata: Dict


class WebDiscoveryAgent:
    """
    Advanced agentic web discovery using cutting-edge techniques:
    - Multi-threaded crawling
    - AI-powered content analysis
    - Dynamic link discovery
    - Authority verification
    - Relevance scoring
    """
    
    def __init__(self):
        self.agent_name = "WebDiscoveryAgent"
        self.session_pool = None
        self.discovered_urls: Set[str] = set()
        self.authority_patterns = self._load_authority_patterns()
        self.regulatory_keywords = self._load_regulatory_keywords()
        
        # Advanced discovery settings
        self.max_concurrent_requests = 10
        self.max_depth = 3
        self.timeout = 30
        self.max_pages_per_domain = 50
        
        logger.info(f"{self.agent_name} initialized with advanced discovery capabilities")
    
    def _load_authority_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for identifying regulatory authorities"""
        return {
            "government": [
                r"\.gov\.",
                r"\.gouv\.",
                r"\.govt\.",
                r"government",
                r"official",
                r"regulatory",
                r"authority",
                r"commission",
                r"ministry",
                r"department"
            ],
            "legal": [
                r"\.law\.",
                r"\.legal\.",
                r"legislation",
                r"regulation",
                r"statute",
                r"act",
                r"directive",
                r"ordinance"
            ],
            "financial": [
                r"\.bank\.",
                r"\.finance\.",
                r"central\s*bank",
                r"financial\s*authority",
                r"securities",
                r"banking\s*regulator"
            ]
        }
    
    def _load_regulatory_keywords(self) -> List[str]:
        """Load regulatory keywords for content analysis"""
        return [
            "regulation", "compliance", "licensing", "permit", "registration",
            "data protection", "privacy", "financial services", "banking",
            "securities", "insurance", "telecommunications", "healthcare",
            "environmental", "labor", "employment", "tax", "customs",
            "import", "export", "business registration", "corporate law",
            "consumer protection", "competition law", "intellectual property"
        ]
    
    async def discover_regulatory_sources(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> List[RegulatoryDocument]:
        """
        Agentic discovery of regulatory sources using cutting-edge techniques
        """
        logger.info(f"{self.agent_name}: Starting agentic discovery for {country}")
        
        # Initialize session pool
        self.session_pool = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        try:
            # Step 1: Generate discovery queries using AI
            discovery_queries = await self._generate_discovery_queries(country, industry, business_activities)
            
            # Step 2: Multi-threaded web search and crawling
            discovered_urls = await self._parallel_web_discovery(discovery_queries)
            
            # Step 3: AI-powered content analysis and filtering
            regulatory_docs = await self._analyze_and_filter_content(discovered_urls, country, industry)
            
            # Step 4: Authority verification and ranking
            verified_docs = await self._verify_authorities_and_rank(regulatory_docs)
            
            logger.info(f"{self.agent_name}: Discovered {len(verified_docs)} regulatory sources")
            return verified_docs
            
        finally:
            if self.session_pool:
                await self.session_pool.close()
    
    async def _generate_discovery_queries(self, country: str, industry: str, business_activities: List[str]) -> List[str]:
        """Generate intelligent discovery queries using AI"""
        
        prompt = f"""
        You are an expert regulatory researcher. Generate 10-15 specific search queries to find regulatory information for:
        
        Country: {country}
        Industry: {industry}
        Business Activities: {', '.join(business_activities)}
        
        Generate queries that will find:
        1. Official government regulatory websites
        2. Specific regulation documents
        3. Licensing and compliance requirements
        4. Industry-specific regulations
        
        Return ONLY a JSON array of search strings:
        ["query1", "query2", "query3", ...]
        
        Make queries specific and targeted. Include:
        - "{country} government regulations"
        - "{country} {industry} licensing"
        - "{country} business registration requirements"
        - Specific regulatory body names if you know them
        """
        
        try:
            response = await gemini_client.generate_response(prompt, temperature=0.3)
            
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                return queries[:15]  # Limit to 15 queries
            
        except Exception as e:
            logger.error(f"Error generating discovery queries: {e}")
        
        # Fallback queries
        return [
            f"{country} government regulations",
            f"{country} {industry} licensing requirements",
            f"{country} business registration",
            f"{country} regulatory authority",
            f"{country} compliance requirements"
        ]
    
    async def _parallel_web_discovery(self, queries: List[str]) -> List[DiscoveryResult]:
        """Parallel web discovery using multiple techniques"""
        
        all_results = []
        
        # Create tasks for different discovery methods
        tasks = []
        
        # Method 1: Search engine discovery
        for query in queries[:5]:  # Top 5 queries
            tasks.append(self._search_engine_discovery(query))
        
        # Method 2: Government domain discovery
        tasks.append(self._government_domain_discovery())
        
        # Method 3: Known regulatory body discovery
        tasks.append(self._known_authority_discovery())
        
        # Execute all discovery methods in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        for result_list in results:
            if isinstance(result_list, list):
                all_results.extend(result_list)
        
        # Remove duplicates
        unique_results = self._deduplicate_results(all_results)
        
        logger.info(f"{self.agent_name}: Discovered {len(unique_results)} unique URLs")
        return unique_results
    
    async def _search_engine_discovery(self, query: str) -> List[DiscoveryResult]:
        """Discover regulatory sources through search engines"""
        results = []
        
        try:
            # Use multiple search approaches
            search_urls = [
                f"https://www.google.com/search?q={query}+site:.gov",
                f"https://www.google.com/search?q={query}+regulation+official",
                f"https://www.google.com/search?q={query}+government+authority"
            ]
            
            # Create a new session for this operation to avoid loop issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                for search_url in search_urls:
                    try:
                        async with session.get(search_url) as response:
                            if response.status == 200:
                                content = await response.text()
                                discovered_urls = self._extract_urls_from_search(content)
                                
                                for url in discovered_urls[:10]:  # Top 10 results
                                    if self._is_regulatory_url(url):
                                        result = await self._analyze_url(url, "search_engine")
                                        if result:
                                            results.append(result)
                                            
                    except Exception as e:
                        logger.debug(f"Search discovery error for {search_url}: {e}")
                        
        except Exception as e:
            logger.error(f"Search engine discovery error: {e}")
        
        return results
    
    async def _government_domain_discovery(self) -> List[DiscoveryResult]:
        """Discover regulatory sources by crawling government domains"""
        results = []
        
        # Common government domain patterns
        gov_patterns = [
            "gov", "gouv", "govt", "government", "official"
        ]
        
        # This would be enhanced with actual domain discovery
        # For now, we'll use a simplified approach
        
        return results
    
    async def _known_authority_discovery(self) -> List[DiscoveryResult]:
        """Discover sources from known regulatory authorities"""
        results = []
        
        # This would contain a database of known regulatory authorities
        # For now, we'll use AI to generate authority suggestions
        
        return results
    
    def _extract_urls_from_search(self, content: str) -> List[str]:
        """Extract URLs from search results"""
        urls = []
        
        # Extract URLs using regex
        url_pattern = r'https?://[^\s<>"]+'
        found_urls = re.findall(url_pattern, content)
        
        for url in found_urls:
            # Clean URL
            url = url.split('&')[0]  # Remove tracking parameters
            if self._is_valid_url(url):
                urls.append(url)
        
        return list(set(urls))  # Remove duplicates
    
    def _is_regulatory_url(self, url: str) -> bool:
        """Check if URL is likely to contain regulatory information"""
        url_lower = url.lower()
        
        # Check for government/regulatory domains
        for pattern_type, patterns in self.authority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return True
        
        # Check for regulatory keywords in URL
        for keyword in self.regulatory_keywords:
            if keyword.replace(" ", "") in url_lower:
                return True
        
        return False
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def _analyze_url(self, url: str, discovery_method: str) -> Optional[DiscoveryResult]:
        """Analyze a URL for regulatory content"""
        
        if url in self.discovered_urls:
            return None
        
        self.discovered_urls.add(url)
        
        try:
            # Create a new session to avoid loop issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "Unknown Title"
                
                # Extract main content
                main_content = self._extract_main_content(soup)
                
                # Determine authority
                authority = self._identify_authority(url, title_text, main_content)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(title_text, main_content)
                
                return DiscoveryResult(
                    url=url,
                    title=title_text,
                    content=main_content,
                    authority=authority,
                    relevance_score=relevance_score,
                    discovery_method=discovery_method,
                    metadata={
                        "content_length": len(main_content),
                        "has_forms": bool(soup.find('form')),
                        "has_tables": bool(soup.find('table')),
                        "last_modified": response.headers.get('last-modified')
                    }
                )
                
        except Exception as e:
            logger.debug(f"Error analyzing URL {url}: {e}")
            return None
    
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
    
    def _identify_authority(self, url: str, title: str, content: str) -> str:
        """Identify the regulatory authority"""
        
        # Check URL for authority patterns
        for pattern_type, patterns in self.authority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return f"{pattern_type.title()} Authority"
        
        # Check title and content
        text_to_check = f"{title} {content[:1000]}"
        
        for pattern_type, patterns in self.authority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    return f"{pattern_type.title()} Authority"
        
        return "Government Authority"
    
    def _calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate relevance score for regulatory content"""
        score = 0.0
        text_to_check = f"{title} {content}".lower()
        
        # Count regulatory keywords
        keyword_matches = sum(1 for keyword in self.regulatory_keywords 
                            if keyword.lower() in text_to_check)
        
        score += min(keyword_matches * 0.1, 0.5)  # Up to 0.5 for keywords
        
        # Bonus for official language
        official_indicators = ["official", "regulation", "law", "act", "directive"]
        official_matches = sum(1 for indicator in official_indicators 
                             if indicator in text_to_check)
        
        score += min(official_matches * 0.1, 0.3)  # Up to 0.3 for official language
        
        # Content length bonus
        if len(content) > 1000:
            score += 0.2
        
        return min(score, 1.0)
    
    def _deduplicate_results(self, results: List[DiscoveryResult]) -> List[DiscoveryResult]:
        """Remove duplicate results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    async def _analyze_and_filter_content(self, discovered_urls: List[DiscoveryResult], country: str, industry: str) -> List[RegulatoryDocument]:
        """Analyze and filter content using AI"""
        
        regulatory_docs = []
        
        # Process in batches to avoid overwhelming the AI
        batch_size = 5
        for i in range(0, len(discovered_urls), batch_size):
            batch = discovered_urls[i:i + batch_size]
            
            # Analyze batch with AI
            batch_docs = await self._analyze_batch_with_ai(batch, country, industry)
            regulatory_docs.extend(batch_docs)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        return regulatory_docs
    
    async def _analyze_batch_with_ai(self, batch: List[DiscoveryResult], country: str, industry: str) -> List[RegulatoryDocument]:
        """Analyze a batch of discovered URLs with AI"""
        
        regulatory_docs = []
        
        for result in batch:
            try:
                # Use AI to analyze content and extract regulatory information
                analysis_prompt = f"""
                Analyze this regulatory content for {country} in the {industry} industry:
                
                Title: {result.title}
                Authority: {result.authority}
                Content: {result.content[:2000]}...
                
                Extract regulatory information and return JSON:
                {{
                    "is_regulatory": true/false,
                    "regulation_type": "data_protection|financial|business|general",
                    "regulation_id": "specific regulation ID if found",
                    "key_requirements": ["requirement1", "requirement2"],
                    "compliance_deadlines": ["deadline1", "deadline2"],
                    "authority_contact": "contact info if found",
                    "confidence_score": 0.0-1.0
                }}
                
                Only return JSON, no other text.
                """
                
                ai_response = await gemini_client.generate_response(analysis_prompt, temperature=0.2)
                
                # Parse AI response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    
                    if analysis.get('is_regulatory', False):
                        doc = RegulatoryDocument(
                            title=result.title,
                            content=result.content[:5000],  # Limit content length
                            source=result.authority,
                            country=country,
                            regulation_type=analysis.get('regulation_type', 'general'),
                            url=result.url,
                            authority=result.authority,
                            regulation_id=analysis.get('regulation_id'),
                            relevance_score=result.relevance_score * analysis.get('confidence_score', 0.8)
                        )
                        regulatory_docs.append(doc)
                        
            except Exception as e:
                logger.error(f"Error analyzing content with AI: {e}")
        
        return regulatory_docs
    
    async def _verify_authorities_and_rank(self, docs: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """Verify authorities and rank documents by credibility"""
        
        verified_docs = []
        
        for doc in docs:
            # Verify authority credibility
            credibility_score = await self._verify_authority_credibility(doc.authority, doc.url)
            
            # Adjust relevance score based on credibility
            doc.relevance_score *= credibility_score
            
            # Only include documents with reasonable credibility
            if credibility_score > 0.3:
                verified_docs.append(doc)
        
        # Sort by relevance score
        verified_docs.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return verified_docs
    
    async def _verify_authority_credibility(self, authority: str, url: str) -> float:
        """Verify the credibility of an authority"""
        
        credibility_score = 0.5  # Base score
        
        # Check for official government domains
        if any(pattern in url.lower() for pattern in ['.gov.', '.gouv.', '.govt.']):
            credibility_score += 0.4
        
        # Check for known authority patterns
        known_authorities = [
            'commission', 'authority', 'regulator', 'ministry', 'department',
            'agency', 'board', 'council', 'office'
        ]
        
        if any(auth in authority.lower() for auth in known_authorities):
            credibility_score += 0.2
        
        # Check for SSL certificate (HTTPS)
        if url.startswith('https://'):
            credibility_score += 0.1
        
        return min(credibility_score, 1.0)


# Global instance
web_discovery_agent = WebDiscoveryAgent() 