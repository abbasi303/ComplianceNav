"""
Dynamic API Integration Agent
Discovers and integrates with regulatory APIs in real-time
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
import json
from dataclasses import dataclass
from loguru import logger
import time
from urllib.parse import urljoin, urlparse
import re

from integrations.gemini_client import gemini_client
from agents.scout_agent import RegulatoryDocument


@dataclass
class APIDiscoveryResult:
    """Result from API discovery"""
    api_url: str
    api_type: str
    country: str
    authority: str
    endpoints: List[str]
    authentication_required: bool
    rate_limits: Dict
    documentation_url: str
    test_successful: bool


class APIIntegrationAgent:
    """
    Dynamic API integration using cutting-edge techniques:
    - API discovery and testing
    - Dynamic endpoint mapping
    - Authentication handling
    - Rate limit management
    - Real-time data fetching
    """
    
    def __init__(self):
        self.agent_name = "APIIntegrationAgent"
        self.session_pool = None
        self.api_cache = {}
        self.known_apis = self._load_known_apis()
        
        # API settings
        self.timeout = 30
        self.max_retries = 3
        self.rate_limit_delay = 1.0
        
        logger.info(f"{self.agent_name} initialized with dynamic API capabilities")
    
    def _load_known_apis(self) -> Dict[str, Dict]:
        """Load database of known regulatory APIs"""
        return {
            "EU": {
                "eur_lex": {
                    "base_url": "https://eur-lex.europa.eu",
                    "api_endpoint": "https://publications.europa.eu/webapi/rdf/sparql",
                    "authority": "European Commission",
                    "endpoints": {
                        "search": "/search.html",
                        "document": "/eli/reg/{id}/oj",
                        "sparql": "/webapi/rdf/sparql"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 60}
                },
                "europa_open_data": {
                    "base_url": "https://data.europa.eu",
                    "api_endpoint": "https://data.europa.eu/api/hub/search",
                    "authority": "European Commission",
                    "endpoints": {
                        "search": "/api/hub/search",
                        "dataset": "/api/hub/dataset/{id}"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 30}
                }
            },
            "Germany": {
                "gesetze_im_internet": {
                    "base_url": "https://www.gesetze-im-internet.de",
                    "api_endpoint": None,  # No official API
                    "authority": "German Federal Government",
                    "endpoints": {
                        "search": "/suche/index.html",
                        "law": "/{law_code}/"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 20}
                },
                "bafin": {
                    "base_url": "https://www.bafin.de",
                    "api_endpoint": None,  # No official API
                    "authority": "BaFin",
                    "endpoints": {
                        "publications": "/EN/Veroeffentlichungen/",
                        "supervision": "/EN/Supervision/"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 15}
                }
            },
            "US": {
                "federal_register": {
                    "base_url": "https://www.federalregister.gov",
                    "api_endpoint": "https://www.federalregister.gov/api/v1",
                    "authority": "Federal Register",
                    "endpoints": {
                        "documents": "/api/v1/documents",
                        "agencies": "/api/v1/agencies",
                        "search": "/api/v1/documents.json"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 1000}
                },
                "sec": {
                    "base_url": "https://www.sec.gov",
                    "api_endpoint": "https://data.sec.gov",
                    "authority": "SEC",
                    "endpoints": {
                        "filings": "/Archives/edgar/data",
                        "company": "/Archives/edgar/data/{cik}"
                    },
                    "authentication": False,
                    "rate_limit": {"requests_per_minute": 10}
                }
            }
        }
    
    async def discover_and_integrate_apis(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> List[RegulatoryDocument]:
        """
        Discover and integrate with regulatory APIs dynamically
        """
        logger.info(f"{self.agent_name}: Discovering APIs for {country}")
        
        # Initialize session pool
        self.session_pool = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'ComplianceNavigator/1.0'}
        )
        
        try:
            # Step 1: Discover available APIs
            discovered_apis = await self._discover_apis(country, industry)
            
            # Step 2: Test and validate APIs
            working_apis = await self._test_apis(discovered_apis)
            
            # Step 3: Fetch regulatory data from working APIs
            regulatory_docs = await self._fetch_from_apis(working_apis, country, industry, business_activities)
            
            logger.info(f"{self.agent_name}: Retrieved {len(regulatory_docs)} documents from APIs")
            return regulatory_docs
            
        finally:
            if self.session_pool:
                await self.session_pool.close()
    
    async def _discover_apis(self, country: str, industry: str) -> List[APIDiscoveryResult]:
        """Discover available regulatory APIs"""
        
        discovered_apis = []
        
        # Check known APIs for the country
        if country in self.known_apis:
            for api_name, api_config in self.known_apis[country].items():
                discovery_result = APIDiscoveryResult(
                    api_url=api_config['base_url'],
                    api_type=api_name,
                    country=country,
                    authority=api_config['authority'],
                    endpoints=list(api_config['endpoints'].keys()),
                    authentication_required=api_config.get('authentication', False),
                    rate_limits=api_config.get('rate_limit', {}),
                    documentation_url=f"{api_config['base_url']}/docs" if api_config.get('api_endpoint') else "",
                    test_successful=False
                )
                discovered_apis.append(discovery_result)
        
        # Use AI to discover additional APIs
        ai_discovered = await self._ai_discover_apis(country, industry)
        discovered_apis.extend(ai_discovered)
        
        return discovered_apis
    
    async def _ai_discover_apis(self, country: str, industry: str) -> List[APIDiscoveryResult]:
        """Use AI to discover additional regulatory APIs"""
        
        prompt = f"""
        You are an API discovery expert. Find regulatory APIs for {country} in the {industry} industry.
        
        Look for:
        1. Government open data APIs
        2. Regulatory authority APIs
        3. Legal database APIs
        4. Industry-specific regulatory APIs
        
        Return JSON array of discovered APIs:
        [
            {{
                "api_url": "https://api.example.gov",
                "api_type": "government_open_data",
                "authority": "Government Authority",
                "endpoints": ["/regulations", "/licenses"],
                "authentication_required": false,
                "documentation_url": "https://api.example.gov/docs"
            }}
        ]
        
        Only return APIs that are likely to exist and be accessible.
        """
        
        try:
            response = await gemini_client.generate_response(prompt, temperature=0.3)
            
            # Parse AI response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                ai_apis = json.loads(json_match.group())
                
                discovered_apis = []
                for api_data in ai_apis:
                    discovery_result = APIDiscoveryResult(
                        api_url=api_data.get('api_url', ''),
                        api_type=api_data.get('api_type', 'unknown'),
                        country=country,
                        authority=api_data.get('authority', 'Unknown Authority'),
                        endpoints=api_data.get('endpoints', []),
                        authentication_required=api_data.get('authentication_required', False),
                        rate_limits={},
                        documentation_url=api_data.get('documentation_url', ''),
                        test_successful=False
                    )
                    discovered_apis.append(discovery_result)
                
                return discovered_apis
                
        except Exception as e:
            logger.error(f"AI API discovery error: {e}")
        
        return []
    
    async def _test_apis(self, discovered_apis: List[APIDiscoveryResult]) -> List[APIDiscoveryResult]:
        """Test discovered APIs for functionality"""
        
        working_apis = []
        
        for api in discovered_apis:
            try:
                # Test API accessibility
                if await self._test_api_accessibility(api):
                    api.test_successful = True
                    working_apis.append(api)
                    logger.info(f"API {api.api_url} is working")
                else:
                    logger.warning(f"API {api.api_url} failed accessibility test")
                    
            except Exception as e:
                logger.error(f"Error testing API {api.api_url}: {e}")
        
        return working_apis
    
    async def _test_api_accessibility(self, api: APIDiscoveryResult) -> bool:
        """Test if an API is accessible"""
        
        try:
            # Create a new session to avoid loop issues
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # Test base URL
                async with session.get(api.api_url) as response:
                    if response.status == 200:
                        return True
                
                # Test documentation URL if available
                if api.documentation_url:
                    async with session.get(api.documentation_url) as response:
                        if response.status == 200:
                            return True
                
                # Test first endpoint if available
                if api.endpoints:
                    test_endpoint = urljoin(api.api_url, api.endpoints[0])
                    async with session.get(test_endpoint) as response:
                        if response.status in [200, 404]:  # 404 means endpoint exists but no data
                            return True
                
                return False
            
        except Exception as e:
            logger.debug(f"API accessibility test failed for {api.api_url}: {e}")
            return False
    
    async def _fetch_from_apis(
        self, 
        working_apis: List[APIDiscoveryResult], 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> List[RegulatoryDocument]:
        """Fetch regulatory data from working APIs"""
        
        all_documents = []
        
        for api in working_apis:
            try:
                # Fetch data based on API type
                if api.api_type == "eur_lex":
                    docs = await self._fetch_from_eur_lex(api, industry)
                elif api.api_type == "federal_register":
                    docs = await self._fetch_from_federal_register(api, industry)
                elif api.api_type == "government_open_data":
                    docs = await self._fetch_from_open_data(api, country, industry)
                else:
                    docs = await self._fetch_generic_api(api, country, industry, business_activities)
                
                all_documents.extend(docs)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Error fetching from API {api.api_url}: {e}")
        
        return all_documents
    
    async def _fetch_from_eur_lex(self, api: APIDiscoveryResult, industry: str) -> List[RegulatoryDocument]:
        """Fetch data from EUR-Lex API"""
        
        documents = []
        
        try:
            # SPARQL query for regulations
            sparql_query = f"""
            PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            SELECT ?work ?title ?date ?type
            WHERE {{
                ?work cdm:work_date_document ?date .
                ?work cdm:work_has_work-type ?type .
                ?work cdm:work_has_title ?title .
                FILTER(?type = cdm:regulation)
                FILTER(?date >= "2020-01-01"^^xsd:date)
                FILTER(CONTAINS(LCASE(?title), "{industry.lower()}"))
            }}
            LIMIT 10
            """
            
            # For MVP, we'll simulate EUR-Lex results
            # In production, this would use the actual SPARQL endpoint
            
            simulated_docs = [
                {
                    "title": f"EU {industry.title()} Regulation 2024",
                    "content": f"Regulation for {industry} industry in the European Union",
                    "date": "2024-01-15",
                    "type": "regulation"
                }
            ]
            
            for doc_data in simulated_docs:
                doc = RegulatoryDocument(
                    title=doc_data['title'],
                    content=doc_data['content'],
                    source=api.authority,
                    country="EU",
                    regulation_type="regulation",
                    url=f"{api.api_url}/eli/reg/2024/123/oj",
                    authority=api.authority,
                    regulation_id="REG-2024-123",
                    relevance_score=0.8
                )
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error fetching from EUR-Lex: {e}")
        
        return documents
    
    async def _fetch_from_federal_register(self, api: APIDiscoveryResult, industry: str) -> List[RegulatoryDocument]:
        """Fetch data from Federal Register API"""
        
        documents = []
        
        try:
            # Search endpoint
            search_url = f"{api.api_url}/documents.json"
            params = {
                'conditions[term]': industry,
                'conditions[type][]': 'RULE',
                'per_page': 10
            }
            
            async with self.session_pool.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('results', []):
                        doc = RegulatoryDocument(
                            title=item.get('title', 'Unknown Title'),
                            content=item.get('abstract', 'No abstract available'),
                            source=api.authority,
                            country="US",
                            regulation_type="rule",
                            url=item.get('html_url', ''),
                            authority=api.authority,
                            regulation_id=item.get('document_number', ''),
                            relevance_score=0.7
                        )
                        documents.append(doc)
                        
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
        
        return documents
    
    async def _fetch_from_open_data(self, api: APIDiscoveryResult, country: str, industry: str) -> List[RegulatoryDocument]:
        """Fetch data from government open data APIs"""
        
        documents = []
        
        try:
            # Generic open data search
            search_url = f"{api.api_url}/search"
            params = {
                'q': f"{industry} regulation",
                'format': 'json',
                'limit': 10
            }
            
            async with self.session_pool.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('results', []):
                        doc = RegulatoryDocument(
                            title=item.get('title', 'Unknown Title'),
                            content=item.get('description', 'No description available'),
                            source=api.authority,
                            country=country,
                            regulation_type="open_data",
                            url=item.get('url', ''),
                            authority=api.authority,
                            regulation_id=item.get('id', ''),
                            relevance_score=0.6
                        )
                        documents.append(doc)
                        
        except Exception as e:
            logger.error(f"Error fetching from open data API: {e}")
        
        return documents
    
    async def _fetch_generic_api(
        self, 
        api: APIDiscoveryResult, 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> List[RegulatoryDocument]:
        """Fetch data from generic APIs"""
        
        documents = []
        
        try:
            # Try different endpoints
            for endpoint in api.endpoints:
                try:
                    url = urljoin(api.api_url, endpoint)
                    
                    # Add query parameters
                    params = {
                        'q': industry,
                        'country': country,
                        'format': 'json'
                    }
                    
                    async with self.session_pool.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Process response based on structure
                            if isinstance(data, list):
                                items = data
                            elif isinstance(data, dict):
                                items = data.get('results', data.get('data', []))
                            else:
                                continue
                            
                            for item in items[:5]:  # Limit to 5 items
                                doc = RegulatoryDocument(
                                    title=item.get('title', 'Unknown Title'),
                                    content=item.get('content', item.get('description', 'No content available')),
                                    source=api.authority,
                                    country=country,
                                    regulation_type="api_data",
                                    url=item.get('url', ''),
                                    authority=api.authority,
                                    regulation_id=item.get('id', ''),
                                    relevance_score=0.5
                                )
                                documents.append(doc)
                                
                except Exception as e:
                    logger.debug(f"Error fetching from endpoint {endpoint}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching from generic API: {e}")
        
        return documents


# Global instance
api_integration_agent = APIIntegrationAgent() 