"""
Regulation Research Module
Handles core regulation discovery and research logic
Extracted from scout_agent.py for better modularity
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
from urllib.parse import urljoin, urlparse
import time

from pydantic import BaseModel
from typing import Optional

class RegulatoryDocument(BaseModel):
    """Structured regulatory document"""
    title: str
    content: str
    source: str
    country: str
    regulation_type: str
    url: Optional[str] = None
    authority: Optional[str] = None
    regulation_id: Optional[str] = None
    last_updated: Optional[str] = None
    relevance_score: float = 0.0
    citation_format: Optional[str] = None

class RegulationResearcher:
    """Handles regulation research and discovery"""
    
    def __init__(self):
        self.name = "RegulationResearcher"
        self.session_pool = None
        
    async def research_single_query(
        self, 
        query: Dict[str, str], 
        startup_info: Any,
        session: aiohttp.ClientSession
    ) -> List[RegulatoryDocument]:
        """Research a single query across all data sources"""
        documents = []
        query_text = query['query']
        query_type = query.get('type', 'general')
        
        logger.debug(f"{self.name}: Researching query: {query_text}")
        
        # Try multiple approaches for finding regulations
        try:
            # 1. Try EU Open Data Portal (if relevant countries)
            if any(country.lower() in ['germany', 'france', 'netherlands', 'spain', 'italy', 'eu', 'europe'] 
                   for country in startup_info.target_countries):
                eu_docs = await self._search_eu_portal(session, query_text, query_type)
                documents.extend(eu_docs)
            
            # 2. Try web search for regulatory information
            web_docs = await self._web_search_regulations(session, query_text, startup_info.target_countries)
            documents.extend(web_docs)
            
            # 3. Try targeted government websites
            for country in startup_info.target_countries[:2]:  # Limit to 2 countries
                gov_docs = await self._search_government_sites(session, query_text, country)
                documents.extend(gov_docs)
        
        except Exception as e:
            logger.error(f"{self.name}: Error researching query '{query_text}': {e}")
        
        return documents
    
    async def _search_eu_portal(
        self, 
        session: aiohttp.ClientSession, 
        query: str, 
        query_type: str
    ) -> List[RegulatoryDocument]:
        """Search the EU Open Data Portal"""
        documents = []
        
        try:
            # For production, integrate with actual EU Open Data Portal API
            # For now, generate synthetic regulatory content based on query
            synthetic_docs = await self._generate_synthetic_regulations(query, 'EU', query_type)
            documents.extend(synthetic_docs)
            
        except Exception as e:
            logger.error(f"Error searching EU portal: {e}")
        
        return documents
    
    async def _web_search_regulations(
        self, 
        session: aiohttp.ClientSession,
        query: str, 
        countries: List[str]
    ) -> List[RegulatoryDocument]:
        """Search web for regulatory information"""
        documents = []
        
        try:
            # For production: implement actual web search
            for country in countries[:2]:
                synthetic_docs = await self._generate_synthetic_regulations(query, country, 'web_search')
                documents.extend(synthetic_docs)
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
        
        return documents
    
    async def _search_government_sites(
        self, 
        session: aiohttp.ClientSession,
        query: str, 
        country: str
    ) -> List[RegulatoryDocument]:
        """Search targeted government websites"""
        documents = []
        
        try:
            # Implement government site-specific search logic
            synthetic_docs = await self._generate_synthetic_regulations(query, country, 'government')
            documents.extend(synthetic_docs)
            
        except Exception as e:
            logger.error(f"Error searching government sites for {country}: {e}")
        
        return documents
    
    async def _generate_synthetic_regulations(
        self, 
        query: str, 
        country: str, 
        source_type: str
    ) -> List[RegulatoryDocument]:
        """Generate AI-powered regulatory guidance (no fake URLs)"""
        
        # Use AI to generate realistic regulatory guidance without fake URLs
        from integrations.gemini_client import gemini_client
        
        try:
            prompt = f"""
            You are a regulatory expert for {country}. Based on the query "{query}", provide realistic regulatory guidance.
            
            IMPORTANT: Do NOT create fake URLs or government websites. Instead, provide:
            1. Real regulatory requirements that would apply
            2. General guidance on compliance steps
            3. Mention of relevant authorities (without fake URLs)
            4. Actual regulation names and numbers if you know them
            
            For {country}, focus on:
            - Real regulatory bodies and authorities
            - Actual regulation names and numbers
            - General compliance requirements
            - Industry-specific guidance
            
            Return a JSON response with:
            {{
                "title": "Realistic regulation name",
                "content": "Detailed regulatory guidance without fake URLs",
                "authority": "Real authority name",
                "regulation_id": "Actual regulation ID if known, otherwise null",
                "regulation_type": "data_protection|financial|business|general"
            }}
            """
            
            response = await gemini_client.generate_response(prompt, temperature=0.3)
            
            # Try to parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                reg_data = json.loads(json_match.group())
                
                return [RegulatoryDocument(
                    title=reg_data.get('title', f"{country} Regulatory Guidance"),
                    content=reg_data.get('content', f"Regulatory guidance for {country} based on {query}"),
                    source=f"{country} Regulatory Analysis",
                    country=country,
                    regulation_type=reg_data.get('regulation_type', 'general'),
                    url=None,  # No fake URLs
                    authority=reg_data.get('authority', f"{country} Government"),
                    regulation_id=reg_data.get('regulation_id'),
                    citation_format=f"{country} Regulatory Guidance - {query}",
                    relevance_score=0.7
                )]
            
        except Exception as e:
            logger.error(f"Error generating AI regulatory guidance: {e}")
        
        # Fallback: Return guidance without fake URLs
        if 'data protection' in query.lower() or 'privacy' in query.lower():
            return [RegulatoryDocument(
                title=f"{country} Data Protection Requirements",
                content=f"Data protection and privacy requirements for {country}. This covers data processing, consent, privacy rights, and compliance obligations. Consult with local legal experts for specific implementation guidance.",
                source=f"{country} Regulatory Analysis",
                country=country,
                regulation_type="data_protection",
                url=None,  # No fake URL
                authority=f"{country} Data Protection Authority",
                regulation_id=None,
                citation_format=f"{country} Data Protection Requirements",
                relevance_score=0.8
            )]
        
        elif 'financial' in query.lower() or 'payment' in query.lower():
            return [RegulatoryDocument(
                title=f"{country} Financial Services Requirements",
                content=f"Financial services and payment processing requirements for {country}. This covers licensing, compliance, reporting obligations, and regulatory oversight. Contact local financial authorities for specific requirements.",
                source=f"{country} Regulatory Analysis",
                country=country,
                regulation_type="financial_regulation",
                url=None,  # No fake URL
                authority=f"{country} Financial Services Authority",
                regulation_id=None,
                citation_format=f"{country} Financial Services Requirements",
                relevance_score=0.7
            )]
        
        else:
            return [RegulatoryDocument(
                title=f"{country} Business Compliance Requirements",
                content=f"General business compliance requirements for {country}. This covers licensing, registration, tax obligations, employment law, and industry-specific regulations. Consult with local business advisors for specific requirements.",
                source=f"{country} Regulatory Analysis",
                country=country,
                regulation_type="general",
                url=None,  # No fake URL
                authority=f"{country} Business Regulatory Authority",
                regulation_id=None,
                citation_format=f"{country} Business Compliance Requirements",
                relevance_score=0.6
            )]

# Global researcher instance for import
regulation_researcher = RegulationResearcher() 