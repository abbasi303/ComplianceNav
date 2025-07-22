"""
Dynamic Research Agent
Discovers regulations for ANY country without hardcoded data
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup
from integrations.gemini_client import gemini_client
import re
import json

class CountryProfile(BaseModel):
    """Dynamic country regulatory profile"""
    country: str
    official_domains: List[str]  # e.g., [".gov.pk", ".secp.gov.pk"]
    regulatory_authorities: List[str]  # e.g., ["SECP", "SBP", "PTA"]
    government_websites: List[str]  # Discovered dynamically
    legal_system: str  # e.g., "common law", "civil law"
    primary_language: str

class DynamicResearchAgent:
    """Agent that can discover regulations for ANY country dynamically"""
    
    def __init__(self):
        self.agent_name = "DynamicResearchAgent"
        self.discovered_countries = {}  # Cache discovered info
        logger.info(f"{self.agent_name} initialized for global regulatory discovery")
    
    async def discover_country_regulations(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> List[Dict]:
        """Discover regulations for any country dynamically"""
        
        logger.info(f"{self.agent_name}: Discovering regulations for {industry} startup in {country}")
        
        # Step 1: Create country profile
        country_profile = await self._discover_country_profile(country)
        
        # Step 2: Find official regulatory sources
        official_sources = await self._discover_official_sources(country_profile, industry)
        
        # Step 3: Research relevant regulations
        regulations = await self._research_country_regulations(
            country_profile, official_sources, industry, business_activities
        )
        
        # Step 4: Validate and structure findings
        validated_regulations = await self._validate_discovered_regulations(regulations, country)
        
        return validated_regulations
    
    async def _discover_country_profile(self, country: str) -> CountryProfile:
        """Discover basic information about a country's regulatory system"""
        
        if country in self.discovered_countries:
            logger.info(f"Using cached profile for {country}")
            return self.discovered_countries[country]
        
        discovery_prompt = f"""
        You are a global regulatory research expert. Analyze the regulatory landscape for {country}.
        
        Research and provide:
        1. Official government domain patterns (e.g., .gov.pk, .gov.in)
        2. Key regulatory authorities (e.g., SECP for Pakistan securities)
        3. Primary government/regulatory websites
        4. Legal system type (common law, civil law, etc.)
        5. Primary official language for laws
        
        Focus on REAL, OFFICIAL sources. Be specific about authority names and domains.
        
        Return a structured analysis with specific details.
        """
        
        try:
            response = await gemini_client.generate_response(
                discovery_prompt,
                temperature=0.2,  # Low temperature for factual accuracy
                system_prompt="You are an expert in global regulatory systems. Provide accurate, specific information about official government sources."
            )
            
            # Parse the response to extract structured data
            profile_data = await self._parse_country_profile(response, country)
            
            profile = CountryProfile(**profile_data)
            
            # Cache the discovered profile
            self.discovered_countries[country] = profile
            
            logger.info(f"Discovered profile for {country}: {len(profile.regulatory_authorities)} authorities")
            return profile
            
        except Exception as e:
            logger.error(f"Error discovering country profile for {country}: {e}")
            return self._create_fallback_profile(country)
    
    async def _discover_official_sources(
        self, 
        country_profile: CountryProfile, 
        industry: str
    ) -> List[Dict]:
        """Discover official regulatory sources for the industry"""
        
        logger.info(f"Discovering official sources for {industry} in {country_profile.country}")
        
        source_discovery_prompt = f"""
        Find the specific official regulatory sources for a {industry} business in {country_profile.country}.
        
        Known regulatory authorities: {country_profile.regulatory_authorities}
        Official domains: {country_profile.official_domains}
        
        For each relevant authority, find:
        1. Specific website URL
        2. Regulatory section relevant to {industry}
        3. Laws/regulations that apply
        4. Contact information if available
        
        Focus on {industry}-specific requirements like:
        - Business licensing
        - Data protection
        - Industry-specific regulations
        - Tax and compliance
        
        Return specific, actionable source information.
        """
        
        try:
            response = await gemini_client.generate_response(source_discovery_prompt, temperature=0.2)
            
            sources = await self._parse_official_sources(response, country_profile)
            
            logger.info(f"Discovered {len(sources)} official sources")
            return sources
            
        except Exception as e:
            logger.error(f"Error discovering official sources: {e}")
            return []
    
    async def _parse_official_sources(self, response: str, country_profile: CountryProfile) -> List[Dict]:
        """Parse AI response to extract official regulatory sources"""
        
        try:
            # Extract JSON from AI response
            import re
            import json
            
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                sources_data = json.loads(json_match.group())
                
                # Convert to standard format
                sources = []
                for source_data in sources_data:
                    source = {
                        'name': source_data.get('name', 'Unknown Authority'),
                        'url': source_data.get('url', ''),
                        'type': source_data.get('type', 'government'),
                        'authority': source_data.get('authority', ''),
                        'description': source_data.get('description', ''),
                        'relevance_score': source_data.get('relevance_score', 0.5)
                    }
                    sources.append(source)
                
                return sources
            
            # Fallback: extract sources from text
            sources = []
            lines = response.split('\n')
            for line in lines:
                if 'http' in line and any(domain in line for domain in country_profile.official_domains):
                    # Extract URL and name from line
                    url_match = re.search(r'https?://[^\s]+', line)
                    if url_match:
                        url = url_match.group()
                        name = line.split('http')[0].strip()
                        if name:
                            sources.append({
                                'name': name,
                                'url': url,
                                'type': 'government',
                                'authority': name,
                                'description': f'Discovered {name}',
                                'relevance_score': 0.7
                            })
            
            return sources
            
        except Exception as e:
            logger.error(f"Error parsing official sources: {e}")
            return []
    
    async def _research_country_regulations(
        self,
        country_profile: CountryProfile,
        official_sources: List[Dict],
        industry: str,
        business_activities: List[str]
    ) -> List[Dict]:
        """Research specific regulations from discovered sources"""
        
        logger.info(f"Researching regulations from {len(official_sources)} sources")
        
        all_regulations = []
        
        async with aiohttp.ClientSession() as session:
            for source in official_sources:
                try:
                    # Dynamic search within each source
                    regulations = await self._search_source_dynamically(
                        session, source, industry, business_activities, country_profile
                    )
                    all_regulations.extend(regulations)
                    
                    # Be respectful with requests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Error searching source {source.get('name', 'Unknown')}: {e}")
                    continue
        
        return all_regulations
    
    async def _search_source_dynamically(
        self,
        session: aiohttp.ClientSession,
        source: Dict,
        industry: str,
        activities: List[str],
        country_profile: CountryProfile
    ) -> List[Dict]:
        """Dynamically search a regulatory source"""
        
        source_url = source.get('url')
        if not source_url:
            return []
        
        logger.info(f"Searching {source.get('name', 'Unknown source')}")
        
        try:
            # Try to access the source website
            async with session.get(source_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Use AI to analyze the website structure and find relevant regulations
                    analysis = await self._analyze_regulatory_website(
                        html[:5000],  # First 5KB for analysis
                        source,
                        industry,
                        country_profile
                    )
                    
                    return analysis.get('regulations', [])
                else:
                    logger.warning(f"Could not access {source_url}: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching {source_url}: {e}")
            return []
    
    async def _analyze_regulatory_website(
        self,
        html_content: str,
        source: Dict,
        industry: str,
        country_profile: CountryProfile
    ) -> Dict:
        """Use AI to analyze a regulatory website and extract relevant information"""
        
        # Clean HTML for analysis
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()[:3000]  # First 3000 chars
        
        analysis_prompt = f"""
        Analyze this regulatory website content for {industry} businesses in {country_profile.country}:
        
        Website: {source.get('name', 'Unknown')}
        URL: {source.get('url', '')}
        Content Preview: {text_content[:1500]}
        
        Extract:
        1. Relevant regulations/laws mentioned
        2. Licensing requirements
        3. Compliance obligations
        4. Links to specific regulatory documents
        5. Contact information for questions
        
        Focus on finding actual regulation names, not general descriptions.
        Return specific, actionable regulatory information.
        """
        
        try:
            response = await gemini_client.generate_response(analysis_prompt, temperature=0.2)
            
            # Parse the AI analysis
            regulations = await self._extract_regulations_from_analysis(response, source)
            
            return {"regulations": regulations}
            
        except Exception as e:
            logger.error(f"Error analyzing website: {e}")
            return {"regulations": []}
    
    async def _validate_discovered_regulations(
        self, 
        regulations: List[Dict], 
        country: str
    ) -> List[Dict]:
        """Validate that discovered regulations are real and current"""
        
        validated = []
        
        for reg in regulations:
            # Basic validation checks
            if self._is_valid_regulation(reg):
                # Enhanced validation using AI
                is_real = await self._verify_regulation_exists(reg, country)
                
                if is_real:
                    # Add metadata
                    reg['discovery_method'] = 'dynamic'
                    reg['validation_status'] = 'verified'
                    reg['last_discovered'] = asyncio.get_event_loop().time()
                    validated.append(reg)
        
        logger.info(f"Validated {len(validated)}/{len(regulations)} discovered regulations")
        return validated
    
    async def _verify_regulation_exists(self, regulation: Dict, country: str) -> bool:
        """Use AI to verify if a regulation actually exists"""
        
        verification_prompt = f"""
        Verify if this regulation actually exists in {country}:
        
        Name: {regulation.get('name', 'Unknown')}
        Authority: {regulation.get('authority', 'Unknown')}
        Description: {regulation.get('description', 'No description')}
        
        Does this regulation exist? Consider:
        1. Is the authority name correct?
        2. Does the regulation name sound authentic?
        3. Does the description match known regulations?
        
        Return 'VERIFIED' if it exists, 'QUESTIONABLE' if uncertain, 'INVALID' if it doesn't exist.
        Provide brief reasoning.
        """
        
        try:
            response = await gemini_client.generate_response(verification_prompt, temperature=0.1)
            
            return 'VERIFIED' in response.upper()
            
        except Exception as e:
            logger.error(f"Error verifying regulation: {e}")
            return False  # Conservative approach
    
    def _is_valid_regulation(self, regulation: Dict) -> bool:
        """Basic validation of regulation structure"""
        required_fields = ['name', 'authority', 'description']
        
        for field in required_fields:
            if not regulation.get(field) or len(str(regulation.get(field)).strip()) < 5:
                return False
        
        return True
    
    async def _parse_country_profile(self, response: str, country: str) -> Dict:
        """Parse AI response into country profile data"""
        
        try:
            # Use AI to extract structured data
            extraction_prompt = f"""
            Extract structured data from this country analysis for {country}:
            
            {response}
            
            Return JSON format with:
            {{
                "country": "{country}",
                "official_domains": [list of domain patterns like .gov.pk],
                "regulatory_authorities": [list of authority names],
                "government_websites": [list of official websites],
                "legal_system": "common law or civil law",
                "primary_language": "language name"
            }}
            
            Return ONLY the JSON object.
            """
            
            structured_response = await gemini_client.generate_response(extraction_prompt, temperature=0.1)
            
            # Try to parse JSON
            import json
            return json.loads(structured_response.strip('```json\n').strip('```').strip())
            
        except Exception as e:
            logger.error(f"Error parsing country profile: {e}")
            return self._create_fallback_profile_dict(country)
    
    def _create_fallback_profile(self, country: str) -> CountryProfile:
        """Create a basic fallback profile"""
        return CountryProfile(
            country=country,
            official_domains=[f".gov.{country.lower()[:2]}"],
            regulatory_authorities=["Government Authority"],
            government_websites=[],
            legal_system="unknown",
            primary_language="English"  # Fallback assumption
        )
    
    def _create_fallback_profile_dict(self, country: str) -> Dict:
        """Create fallback profile as dictionary"""
        return {
            "country": country,
            "official_domains": [f".gov.{country.lower()[:2]}"],
            "regulatory_authorities": ["Government Authority"],
            "government_websites": [],
            "legal_system": "unknown",
            "primary_language": "English"
        }

# Global dynamic research agent
dynamic_research_agent = DynamicResearchAgent() 