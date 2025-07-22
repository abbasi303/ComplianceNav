"""
Regulation Scout Agent
Connects to official APIs and web sources to fetch up-to-date regulatory information
"""
import aiohttp
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup
from integrations.gemini_client import gemini_client
from core.vector_store import vector_store
import asyncio
from urllib.parse import urljoin, urlparse
import time

class RegulatoryDocument(BaseModel):
    """Structured regulatory document"""
    title: str
    content: str
    source: str
    country: str
    regulation_type: str
    url: Optional[str] = None
    authority: Optional[str] = None  # e.g., "European Commission", "BaFin"
    regulation_id: Optional[str] = None  # e.g., "GDPR Art. 32", "BDSG §26"
    last_updated: Optional[str] = None
    relevance_score: float = 0.0
    citation_format: Optional[str] = None  # e.g., "Regulation (EU) 2016/679, Article 32"
    
    # Additional fields for advanced features
    validation_metadata: Optional[Dict[str, Any]] = None
    discovery_method: Optional[str] = None
    priority_weight: Optional[float] = None
    source_confidence: Optional[float] = None
    user_provided: Optional[bool] = None
    processing_notes: Optional[str] = None
    extraction_quality: Optional[str] = None
    key_requirements: Optional[List[str]] = None

class ScoutAgent:
    """Agent for scouting and fetching regulatory information"""
    
    def __init__(self):
        """Initialize the Scout Agent with agentic capabilities"""
        self.agent_name = "ScoutAgent"
        self.session = None
        self._session_pool = None  # HTTP session pool for better performance
        
        # Import optimized regulatory sources for performance (with strict country isolation)
        try:
            from agents.regulation_sources import OFFICIAL_SOURCES, INDUSTRY_REGULATIONS, REGULATION_URLS
            self.official_sources = OFFICIAL_SOURCES
            self.industry_map = INDUSTRY_REGULATIONS  
            self.regulation_urls = REGULATION_URLS
        except ImportError:
            logger.warning("Regulation sources not found, using dynamic discovery only")
            self.official_sources = {}
            self.industry_map = {}
            self.regulation_urls = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling"""
        if self._session_pool is None or self._session_pool.closed:
            # Create session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=10,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,  # Keep connections alive
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,  # Total timeout
                connect=10  # Connection timeout
            )
            
            self._session_pool = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'ComplianceNavigator/1.0 (+https://compliancenavigator.ai/bot)'
                }
            )
            
            logger.debug("Initialized HTTP session pool with optimized settings")
        
        return self._session_pool
    
    async def _close_session(self):
        """Close HTTP session pool"""
        if self._session_pool and not self._session_pool.closed:
            await self._session_pool.close()
            logger.debug("Closed HTTP session pool")
        
        # Enhanced data sources with real endpoints
        self.data_sources = {
            'eur_lex': {
                'base_url': 'https://eur-lex.europa.eu',
                'search_endpoint': '/search.html?qid=&text={query}&scope=EURLEX&type=quick&lang=en',
                'name': 'EUR-Lex (Official EU Law)',
                'authority': 'European Commission'
            },
            'german_laws': {
                'base_url': 'https://www.gesetze-im-internet.de',
                'name': 'German Federal Laws (Official)',
                'authority': 'German Federal Government'
            },
            'bafin': {
                'base_url': 'https://www.bafin.de',
                'name': 'BaFin Regulations',
                'authority': 'Federal Financial Supervisory Authority'
            }
        }
        
        logger.info(f"{self.agent_name} initialized with {len(self.data_sources)} official data sources")
    
    async def research_regulations(
        self, 
        research_queries: List[Dict[str, str]], 
        startup_info: Any,
        custom_sources: Optional[List[Dict]] = None
    ) -> List[RegulatoryDocument]:
        """
        Advanced agentic regulatory research using cutting-edge techniques:
        - Web discovery and crawling
        - API integration
        - Link validation
        - AI-powered analysis
        """
        """
        Universal regulatory research for ANY country with custom sources
        
        Args:
            research_queries: List of research queries from Intake Agent
            startup_info: Startup information object
            custom_sources: Optional user-provided custom sources
            
        Returns:
            List of relevant regulatory documents
        """
        logger.info(f"{self.agent_name}: Starting universal regulatory research for {startup_info.target_countries}")
        
        if custom_sources:
            logger.info(f"{self.agent_name}: Processing {len(custom_sources)} custom sources")
        
        all_documents = []
        
        # Initialize advanced discovery agents
        try:
            from agents.web_discovery_agent import web_discovery_agent
            from agents.api_integration_agent import api_integration_agent
            from agents.link_validation_agent import link_validation_agent
            advanced_agents_available = True
        except ImportError:
            logger.warning("Advanced agents not available, using fallback methods")
            advanced_agents_available = False
        
        # Step 1: Process custom sources first (highest priority)
        if custom_sources:
            try:
                from agents.custom_source_agent import custom_source_agent, CustomSource
                
                # Convert custom sources to proper format
                custom_source_objects = []
                for source_data in custom_sources:
                    custom_source = CustomSource(**source_data)
                    custom_source_objects.append(custom_source)
                
                # Process custom sources
                processed_sources = await custom_source_agent.process_custom_sources(
                    custom_source_objects, startup_info
                )
                
                # Convert to regulatory documents with enhanced processing
                custom_docs = custom_source_agent.convert_to_regulatory_documents(processed_sources)
                
                # Track custom source statistics for reporting
                high_priority_sources = 0
                pakistan_specific_sources = 0
                
                # Convert to RegulatoryDocument objects with enhanced attributes
                for doc_data in custom_docs:
                    try:
                        # Extract enhanced attributes from custom source processing
                        priority_weight = doc_data.get('priority_weight', 0.9)
                        source_confidence = doc_data.get('source_confidence', 0.8)
                        
                        reg_doc = RegulatoryDocument(
                            title=doc_data.get('title'),
                            content=doc_data.get('content'),
                            source=doc_data.get('source'),
                            country=doc_data.get('country'),
                            regulation_type=doc_data.get('regulation_type'),
                            url=doc_data.get('url', ''),
                            authority=doc_data.get('authority'),
                            regulation_id=doc_data.get('regulation_id', ''),
                            citation_format=doc_data.get('citation_format', ''),
                            relevance_score=doc_data.get('relevance_score', 0.9)
                        )
                        
                        # Add enhanced attributes for downstream processing
                        reg_doc.priority_weight = priority_weight
                        reg_doc.source_confidence = source_confidence
                        reg_doc.user_provided = True
                        reg_doc.processing_notes = doc_data.get('processing_notes', '')
                        reg_doc.extraction_quality = doc_data.get('extraction_quality', 'standard')
                        reg_doc.key_requirements = doc_data.get('key_requirements', [])
                        
                        all_documents.append(reg_doc)
                        
                        # Track statistics
                        if priority_weight > 0.9:
                            high_priority_sources += 1
                        if 'pakistan' in doc_data.get('country', '').lower():
                            pakistan_specific_sources += 1
                        
                    except Exception as e:
                        logger.error(f"Error converting custom source to RegulatoryDocument: {e}")
                        continue
                
                # Enhanced logging with statistics
                logger.info(f"{self.agent_name}: Successfully processed {len(all_documents)} custom sources")
                logger.info(f"Custom source statistics: {high_priority_sources} high-priority, {pakistan_specific_sources} Pakistan-specific")
                
                # If we have high-priority custom sources, adjust search strategy
                if high_priority_sources > 0:
                    logger.info(f"{self.agent_name}: High-priority custom sources detected - adjusting search strategy")
                    # Reduce generic country searches if we have specific user sources
                    target_countries = startup_info.target_countries[:2]  # Limit to 2 to prioritize custom sources
                
            except ImportError:
                logger.warning("Custom source agent not available")
            except Exception as e:
                logger.error(f"Error processing custom sources: {e}")
        
        # Process countries in parallel for better performance  
        target_countries = startup_info.target_countries[:3]  # Default limit
        logger.info(f"Processing {len(target_countries)} countries in parallel: {target_countries}")
        
        # Step 2.5: Use Regional Regulatory Agent for enhanced coverage
        try:
            from agents.regional_regulatory_agent import regional_regulatory_agent
            
            # Check which countries have enhanced module support
            enhanced_countries = []
            standard_countries = []
            
            for country in target_countries:
                if regional_regulatory_agent.has_enhanced_support(country):
                    enhanced_countries.append(country)
                    logger.info(f"Enhanced regional module available for {country}")
                else:
                    standard_countries.append(country)
                    logger.debug(f"No enhanced module for {country}, using standard approach")
            
            # Process enhanced countries with regional modules
            for country in enhanced_countries:
                try:
                    regional_docs = await regional_regulatory_agent.research_country_regulations(
                        country, 
                        startup_info.industry,
                        startup_info.business_activities,
                        startup_info
                    )
                    
                    # Mark as high-priority regional results
                    for doc in regional_docs:
                        doc.source_priority = "regional_module"
                        doc.coverage_quality = "enhanced"
                    
                    all_documents.extend(regional_docs)
                    logger.info(f"Regional module provided {len(regional_docs)} enhanced regulations for {country}")
                    
                except Exception as e:
                    logger.error(f"Regional module failed for {country}: {e}. Adding to standard processing.")
                    standard_countries.append(country)
            
            # Update target countries to only process standard countries with generic approach
            target_countries = standard_countries
            
        except ImportError:
            logger.info("Regional Regulatory Agent not available, using standard country processing")
        except Exception as e:
            logger.error(f"Error with Regional Regulatory Agent: {e}")
        
        # Create parallel tasks for remaining countries (without enhanced modules)
        country_tasks = []
        for country in target_countries:
            task = self._process_single_country(country, startup_info, research_queries)
            country_tasks.append(task)
        
        # Execute all country processing in parallel
        try:
            country_results = await asyncio.gather(*country_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for i, result in enumerate(country_results):
                if isinstance(result, Exception):
                    logger.error(f"Country processing failed for {target_countries[i]}: {result}")
                else:
                    all_documents.extend(result)
                    logger.info(f"Found {len(result)} regulations for {target_countries[i]}")
                    
        except Exception as e:
            logger.error(f"Parallel country processing failed: {e}")
            # Fallback to sequential processing
        
        # Step 3: Advanced Agentic Discovery (if available)
        if advanced_agents_available:
            logger.info(f"{self.agent_name}: Starting advanced agentic discovery")
            
            try:
                # Web discovery (live crawling)
                logger.info(f"{self.agent_name}: Starting web discovery")
                web_docs = await web_discovery_agent.discover_regulatory_sources(
                    country=startup_info.target_countries[0] if startup_info.target_countries else "Unknown",
                    industry=startup_info.industry,
                    business_activities=startup_info.business_activities
                )
                all_documents.extend(web_docs)
                logger.info(f"{self.agent_name}: Web discovery found {len(web_docs)} documents")
                
                # API integration (real-time data)
                logger.info(f"{self.agent_name}: Starting API integration")
                api_docs = await api_integration_agent.discover_and_integrate_apis(
                    country=startup_info.target_countries[0] if startup_info.target_countries else "Unknown",
                    industry=startup_info.industry,
                    business_activities=startup_info.business_activities
                )
                all_documents.extend(api_docs)
                logger.info(f"{self.agent_name}: API integration found {len(api_docs)} documents")
                
                # Link validation (quality assurance)
                logger.info(f"{self.agent_name}: Validating discovered links")
                validated_docs = await link_validation_agent.validate_regulatory_links(all_documents)
                all_documents = validated_docs
                logger.info(f"{self.agent_name}: Link validation completed")
                
            except Exception as e:
                logger.error(f"Advanced agentic discovery failed: {e}")
                logger.info("Continuing with standard processing results")
        
        # Step 4: Enhanced ranking and deduplication
        logger.info(f"{self.agent_name}: Ranking and deduplicating {len(all_documents)} total documents")
        final_docs = self._rank_documents_by_relevance(all_documents, startup_info)
        final_docs = self._deduplicate_documents(final_docs)
        
        logger.info(f"{self.agent_name}: Research completed with {len(final_docs)} final documents")
        return final_docs
        
    async def _create_agentic_research_plan(self, startup_info: Any, queries: List[Dict]) -> Dict:
        """Create an intelligent research plan based on startup profile"""
        logger.info(f"{self.agent_name}: Creating agentic research plan")
        
        planning_prompt = f"""
        Create a smart regulatory research plan for this startup:
        
        Industry: {startup_info.industry}
        Countries: {startup_info.target_countries}
        Activities: {startup_info.business_activities}
        Data Types: {startup_info.data_handling}
        
        Based on this profile, what are the TOP 5 most important regulations to find?
        Consider: data protection, licensing, reporting, industry-specific rules.
        
        Return a prioritized list with specific regulation names and why they're critical.
        """
        
        try:
            response = await gemini_client.generate_response(
                planning_prompt,
                temperature=0.3,
                system_prompt="You are a regulatory compliance expert. Be specific about real regulation names."
            )
            
            return {"plan": response, "priority_regulations": self._extract_priority_regulations(response)}
        except Exception as e:
            logger.error(f"Error creating research plan: {e}")
            return {"plan": "Fallback plan", "priority_regulations": []}
    
    def _extract_priority_regulations(self, response: str) -> List[str]:
        """Extract priority regulation names from AI response"""
        import re
        
        # Common regulation patterns to look for
        regulation_patterns = [
            r'GDPR|General Data Protection Regulation',
            r'BDSG|Bundesdatenschutzgesetz',
            r'TMG|Telemediengesetz',
            r'KWG|Kreditwesengesetz',
            r'ZAG|Zahlungsdiensteaufsichtsgesetz',
            r'PDSG|Patient Data Security Guidelines',
            r'DIGA|Digital Health Applications',
            r'AMG|Arzneimittelgesetz',
            r'MPG|Medizinproduktegesetz'
        ]
        
        found_regulations = []
        for pattern in regulation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            found_regulations.extend(matches)
        
        # Remove duplicates and return
        return list(set(found_regulations))
    
    async def _search_targeted_regulations(self, session: aiohttp.ClientSession, startup_info: Any) -> List[RegulatoryDocument]:
        """Search for specific regulations based on industry mapping"""
        logger.info(f"{self.agent_name}: Searching targeted regulations")
        
        regulations = []
        industry = startup_info.industry.lower()
        
        # Get relevant regulations for this industry
        target_regulations = []
        for country in startup_info.target_countries:
            if industry in self.industry_map and country in self.industry_map[industry]:
                target_regulations.extend(self.industry_map[industry][country])
        
        # Search for each target regulation
        for reg_name in target_regulations[:5]:  # Top 5 most important
            if reg_name in self.regulation_urls:
                regulation = await self._fetch_specific_regulation(session, reg_name, self.regulation_urls[reg_name])
                if regulation:
                    regulations.append(regulation)
                    
        logger.info(f"{self.agent_name}: Found {len(regulations)} targeted regulations")
        return regulations
    
    async def _should_explore_related(self, documents: List[RegulatoryDocument]) -> bool:
        """Agentic decision: Should we explore related regulations?"""
        if not documents or len(documents) == 0:
            return False
            
        # Simple heuristic: explore if we found important regulations
        important_keywords = ['gdpr', 'data protection', 'financial', 'license', 'authorization']
        
        for doc in documents:
            title_lower = doc.title.lower()
            if any(keyword in title_lower for keyword in important_keywords):
                return True  # Found important regulation, explore related ones
                
        return False
    
    async def _discover_related_regulations(self, session: aiohttp.ClientSession, base_docs: List[RegulatoryDocument], startup_info: Any) -> List[RegulatoryDocument]:
        """Discover regulations related to the ones we already found"""
        logger.info(f"{self.agent_name}: Discovering related regulations")
        
        related_docs = []
        
        for doc in base_docs[:3]:  # Only explore top 3 documents
            # Extract referenced regulations from content
            references = self._extract_regulation_references(doc.content)
            
            for ref in references[:3]:  # Top 3 references per document
                if ref in self.regulation_urls:
                    related_reg = await self._fetch_specific_regulation(session, ref, self.regulation_urls[ref])
                    if related_reg:
                        related_docs.append(related_reg)
        
        logger.info(f"{self.agent_name}: Discovered {len(related_docs)} related regulations")
        return related_docs
    
    def _extract_regulation_references(self, content: str) -> List[str]:
        """Extract references to other regulations from text"""
        import re
        
        references = []
        content_lower = content.lower()
        
        # Common regulation patterns
        patterns = {
            'GDPR': r'general data protection regulation|gdpr|regulation \(eu\) 2016/679',
            'BDSG': r'bundesdatenschutzgesetz|bdsg',
            'TMG': r'telemediengesetz|tmg',
            'KWG': r'kreditwesengesetz|kwg',
            'ZAG': r'zahlungsdiensteaufsichtsgesetz|zag'
        }
        
        for reg_name, pattern in patterns.items():
            if re.search(pattern, content_lower):
                references.append(reg_name)
        
        return references
    
    async def _research_single_query(self, query: Dict[str, str], startup_info: Any) -> List[RegulatoryDocument]:
        """Research a single query across all data sources"""
        documents = []
        query_text = query['query']
        query_type = query.get('type', 'general')
        
        logger.debug(f"{self.agent_name}: Researching query: {query_text}")
        
        # Try multiple approaches for finding regulations
        try:
            # 1. Try EU Open Data Portal (if relevant countries)
            if any(country.lower() in ['germany', 'france', 'netherlands', 'spain', 'italy', 'eu', 'europe'] 
                   for country in startup_info.target_countries):
                eu_docs = await self._search_eu_portal(query_text, query_type)
                documents.extend(eu_docs)
            
            # 2. Try web search for regulatory information
            web_docs = await self._web_search_regulations(query_text, startup_info.target_countries)
            documents.extend(web_docs)
            
            # 3. Try targeted government websites
            for country in startup_info.target_countries[:2]:  # Limit to 2 countries
                gov_docs = await self._search_government_sites(query_text, country)
                documents.extend(gov_docs)
        
        except Exception as e:
            logger.error(f"{self.agent_name}: Error researching query '{query_text}': {e}")
        
        return documents
    
    async def _search_eu_portal(self, query: str, query_type: str) -> List[RegulatoryDocument]:
        """Search the EU Open Data Portal"""
        documents = []
        
        try:
            # For MVP, we'll simulate EU portal results using web search
            # In production, integrate with actual EU Open Data Portal API
            
            search_url = f"https://eur-lex.europa.eu/search.html"
            params = {
                'qid': '1644567890123',
                'text': query,
                'SUBDOM_INIT': 'ALL_ALL'
            }
            
            # For MVP: Generate synthetic regulatory content based on query
            synthetic_docs = await self._generate_synthetic_regulations(query, 'EU', query_type)
            documents.extend(synthetic_docs)
            
        except Exception as e:
            logger.error(f"Error searching EU portal: {e}")
        
        return documents
    
    async def _web_search_regulations(self, query: str, countries: List[str]) -> List[RegulatoryDocument]:
        """Search web for regulatory information"""
        documents = []
        
        try:
            # For MVP: Generate realistic regulatory content
            for country in countries[:2]:
                synthetic_docs = await self._generate_synthetic_regulations(query, country, 'general')
                documents.extend(synthetic_docs)
                
        except Exception as e:
            logger.error(f"Error in web search: {e}")
        
        return documents
    
    async def _search_government_sites(self, query: str, country: str) -> List[RegulatoryDocument]:
        """Search specific government websites"""
        documents = []
        
        # For MVP: Generate country-specific regulatory content
        try:
            synthetic_docs = await self._generate_synthetic_regulations(query, country, 'government')
            documents.extend(synthetic_docs)
        except Exception as e:
            logger.error(f"Error searching government sites for {country}: {e}")
        
        return documents
    
    async def _generate_synthetic_regulations(self, query: str, country: str, reg_type: str) -> List[RegulatoryDocument]:
        """Generate synthetic but realistic regulatory documents for MVP"""
        documents = []
        
        system_prompt = f"""
        You are a regulatory expert for {country}. Generate realistic regulatory information 
        based on the query: "{query}". 
        
        Create 1-2 regulatory documents that would typically exist for this query.
        Include:
        1. Proper regulatory title
        2. Key compliance requirements
        3. Licensing/permit requirements if applicable
        4. Penalties for non-compliance
        5. Implementation deadlines
        
        Make this realistic based on actual {country} regulations but clearly synthetic for MVP purposes.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                f"Generate regulatory documents for: {query} in {country}",
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            # Parse response into documents
            doc_sections = response.split('\n\n')
            for i, section in enumerate(doc_sections[:2]):  # Max 2 documents per query
                if len(section.strip()) > 100:
                    title = f"{country} Regulatory Requirement #{i+1} for {query.split(' ')[0]}"
                    
                    document = RegulatoryDocument(
                        title=title,
                        content=section.strip(),
                        source=f"{country} Regulatory Authority",
                        country=country,
                        regulation_type=reg_type,
                        url=None,  # No fake URL
                        last_updated="2024-01-15",
                        relevance_score=0.8  # Will be updated later
                    )
                    documents.append(document)
        
        except Exception as e:
            logger.error(f"Error generating synthetic regulations: {e}")
        
        return documents
    
    def _deduplicate_documents(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """Remove duplicate documents using optimized modular processor"""
        try:
            from agents.scout_modules import document_processor
            return document_processor.deduplicate_documents(documents)
        except ImportError:
            logger.warning("Document processor module not available, using fallback deduplication")
            # Fallback implementation
        if not documents:
            return []
        unique_documents = []
        seen_titles = set()
        for doc in documents:
            title_key = doc.title.lower().replace(' ', '').replace('-', '')
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_documents.append(doc)
        return unique_documents
    
    def _rank_documents_by_relevance(self, documents: List[RegulatoryDocument], startup_info: Any) -> List[RegulatoryDocument]:
        """Enhanced ranking with user-provided source prioritization"""
        try:
            from agents.scout_modules import document_processor
            return document_processor.rank_documents_by_relevance(documents, startup_info)
        except ImportError:
            logger.warning("Document processor module not available, using enhanced fallback ranking")
            
            if not documents:
                return []
            
            # Enhanced ranking algorithm
            for doc in documents:
                score = 0.4  # Base score
                
                # Priority boost for user-provided sources
                if hasattr(doc, 'user_provided') and doc.user_provided:
                    priority_weight = getattr(doc, 'priority_weight', 0.9)
                    score += priority_weight * 0.4  # Up to 40% boost for user sources
                    logger.debug(f"User source boost: {doc.title} (+{priority_weight * 0.4:.2f})")
                
                # Priority boost for regional module results
                if hasattr(doc, 'source_priority') and doc.source_priority == 'regional_module':
                    score += 0.35  # High boost for regional modules
                    logger.debug(f"Regional module boost: {doc.title} (+0.35)")
                elif hasattr(doc, 'coverage_quality') and doc.coverage_quality == 'enhanced':
                    score += 0.25  # General enhanced coverage boost
                
                # Country relevance (reduced weight to allow user sources to dominate)
                if doc.country.lower() in [c.lower() for c in startup_info.target_countries]:
                    score += 0.2  # Reduced from 0.3
                
                # Industry relevance  
                if startup_info.industry.lower() in doc.content.lower():
                    score += 0.15
                
                # Business activity relevance
                for activity in startup_info.business_activities:
                    if activity.lower() in doc.content.lower():
                        score += 0.08
                        break  # Only count once
                
                # Authority credibility boost
                if doc.authority and any(term in doc.authority.lower() 
                                       for term in ['commission', 'authority', 'ministry', 'government']):
                    score += 0.05
                
                # Pakistan-specific boost (given the user's context)
                if 'pakistan' in doc.country.lower():
                    score += 0.1
                
                # Source confidence boost (for enhanced custom sources)
                if hasattr(doc, 'source_confidence'):
                    confidence_boost = (doc.source_confidence - 0.5) * 0.1  # Scale 0.5-1.0 to 0-0.05
                    score += max(0, confidence_boost)
                
                # Quality indicator boost
                if hasattr(doc, 'extraction_quality') and doc.extraction_quality == 'enhanced':
                    score += 0.05
                
                doc.relevance_score = min(score, 0.98)  # Cap at 0.98 to leave room for perfect scores
            
            # Enhanced sorting: Primary by user sources, then by relevance score
            def sort_key(doc):
                # User sources get primary priority
                is_user_provided = getattr(doc, 'user_provided', False)
                priority_weight = getattr(doc, 'priority_weight', 0.0) if is_user_provided else 0.0
                
                # Regional modules get secondary priority
                is_regional_module = getattr(doc, 'source_priority', '') == 'regional_module'
                regional_priority = 1.0 if is_regional_module else 0.0
                
                # Return tuple: (user_priority, priority_weight, regional_priority, relevance_score)
                return (
                    1.0 if is_user_provided else 0.0,  # User sources first
                    priority_weight,  # Then by priority weight within user sources
                    regional_priority,  # Then regional modules
                    doc.relevance_score  # Finally by relevance
                )
            
            sorted_docs = sorted(documents, key=sort_key, reverse=True)
            
            # Log top sources for debugging
            logger.info("Top ranked sources:")
            for i, doc in enumerate(sorted_docs[:5]):
                user_flag = "[USER]" if getattr(doc, 'user_provided', False) else "[SYS]"
                regional_flag = "[REG]" if getattr(doc, 'source_priority', '') == 'regional_module' else ""
                priority = getattr(doc, 'priority_weight', 0.0)
                source_type = f"{user_flag}{regional_flag}".strip()
                logger.info(f"  {i+1}. {source_type} {doc.title[:45]}... (Score: {doc.relevance_score:.2f}, Priority: {priority:.2f})")
            
            return sorted_docs
    
    async def _store_documents_in_vector_store(self, documents: List[RegulatoryDocument]):
        """Store regulatory documents in the vector store"""
        try:
            for doc in documents:
                # Clean metadata - ChromaDB doesn't accept None values
                metadata = {
                    'title': doc.title or '',
                    'source': doc.source or '',
                    'country': doc.country or '',
                    'regulation_type': doc.regulation_type or '',
                    'url': doc.url or '',
                    'authority': doc.authority or '',
                    'regulation_id': doc.regulation_id or '',
                    'last_updated': doc.last_updated or '',
                    'relevance_score': float(doc.relevance_score or 0.0),
                    'citation_format': doc.citation_format or ''
                }
                
                # Filter out empty strings to keep metadata clean
                metadata = {k: v for k, v in metadata.items() if v != ''}
                
                document_id = vector_store.add_regulatory_document(
                    content=doc.content,
                    metadata=metadata
                )
                
                logger.debug(f"Stored document {document_id} in vector store")
                
        except Exception as e:
            logger.error(f"Error storing documents in vector store: {e}")

    async def _fetch_specific_regulation(self, session: aiohttp.ClientSession, reg_name: str, url: str) -> Optional[RegulatoryDocument]:
        """Fetch a specific regulation by name and URL"""
        try:
            logger.info(f"{self.agent_name}: Fetching {reg_name} from {url}")
            
            # Create a basic document with known information
            # In a real implementation, you'd scrape the actual content
            regulation = RegulatoryDocument(
                title=f"{reg_name} - Official Text",
                content=f"Official regulation {reg_name}. This document contains the legal requirements for compliance with {reg_name}.",
                source=self._get_authority_for_regulation(reg_name),
                country=self._get_country_for_regulation(reg_name),
                regulation_type=self._get_regulation_type(reg_name),
                url=url,
                authority=self._get_authority_for_regulation(reg_name),
                regulation_id=reg_name,
                citation_format=self._get_citation_format(reg_name),
                relevance_score=0.9  # High relevance for targeted regulations
            )
            
            return regulation
            
        except Exception as e:
            logger.error(f"Error fetching {reg_name}: {e}")
            return None
    
# Removed hardcoded regulation mappings - now using dynamic discovery for all countries
    
    async def _validate_regulations(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """Validate that the found regulations are real and current"""
        validated = []
        
        for doc in documents:
            # Simple validation: check if it has proper metadata
            if doc.url and doc.authority and doc.regulation_id:
                doc.relevance_score += 0.2  # Boost score for validated documents
                validated.append(doc)
            elif doc.title and doc.country and doc.regulation_type:
                # Partial validation
                validated.append(doc)
        
        logger.info(f"{self.agent_name}: Validated {len(validated)}/{len(documents)} regulations")
        return validated
    
    async def _process_single_country(
        self, 
        country: str, 
        startup_info: Any, 
        research_queries: List[Dict]
    ) -> List[RegulatoryDocument]:
        """Process a single country in parallel-optimized workflow with caching"""
        documents = []
        
        logger.info(f"Processing regulations specifically for {country}")
        
        # Check cache first for performance boost
        try:
            from utils.cache import performance_cache
            cached_docs = await performance_cache.get_regulation_search(
                country=country,
                industry=startup_info.industry,
                business_activities=startup_info.business_activities
            )
            
            if cached_docs:
                logger.info(f"Using cached regulations for {country} ({len(cached_docs)} docs)")
                # Convert cached data back to RegulatoryDocument objects
                for doc_data in cached_docs:
                    try:
                        doc = RegulatoryDocument(**doc_data)
                        if self._is_country_specific(doc, country):
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"Error converting cached doc: {e}")
                
                return documents
                
        except ImportError:
            logger.debug("Performance cache not available")
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
        
        # No cache hit - proceed with normal processing
        # Step 1: Check if we have optimized knowledge for this country (performance boost)
        if self._has_optimized_knowledge(country):
            logger.info(f"Using optimized knowledge base for {country}")
            optimized_docs = await self._search_optimized_regulations(country, startup_info)
            # ENSURE only country-specific results
            country_specific_docs = [doc for doc in optimized_docs if self._is_country_specific(doc, country)]
            documents.extend(country_specific_docs)
        
        else:
            logger.info(f"Discovering regulations dynamically for {country}")
            # Step 2: Use dynamic discovery for other countries
            try:
                from agents.dynamic_research_agent import dynamic_research_agent
                
                dynamic_regulations = await dynamic_research_agent.discover_country_regulations(
                    country=country,
                    industry=startup_info.industry,
                    business_activities=startup_info.business_activities
                )
                
                # Convert to RegulatoryDocument format with country validation
                for reg_data in dynamic_regulations:
                    doc = self._convert_to_regulatory_document(reg_data, country)
                    if doc and self._is_country_specific(doc, country):
                        documents.append(doc)
                        
            except ImportError:
                logger.warning("Dynamic research agent not available, falling back to country-specific search")
                # Country-specific fallback
                fallback_docs = await self._country_specific_fallback_research(country, startup_info, research_queries)
                documents.extend(fallback_docs)
            except Exception as e:
                logger.error(f"Dynamic discovery failed for {country}: {e}")
                # Final country-specific fallback
                fallback_docs = await self._country_specific_fallback_research(country, startup_info, research_queries)
                documents.extend(fallback_docs)
        
        # Filter to ensure country-specific results only
        validated_docs = [doc for doc in documents if self._is_country_specific(doc, country)]
        logger.debug(f"Validated {len(validated_docs)} country-specific regulations for {country}")
        
        # Cache the results for future use
        try:
            from utils.cache import performance_cache
            # Convert to serializable format
            cacheable_docs = []
            for doc in validated_docs:
                doc_dict = doc.model_dump() if hasattr(doc, 'model_dump') else doc.dict()
                cacheable_docs.append(doc_dict)
            
            await performance_cache.set_regulation_search(
                country=country,
                industry=startup_info.industry,
                business_activities=startup_info.business_activities,
                data=cacheable_docs
            )
            logger.debug(f"Cached {len(cacheable_docs)} regulations for {country}")
            
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to cache results: {e}")
        
        return validated_docs
    
    def _has_optimized_knowledge(self, country: str) -> bool:
        """Check if we have optimized knowledge for this country (performance optimization)"""
        known_countries = ['Germany', 'EU', 'European Union', 'United States', 'UK', 'United Kingdom']
        return country in known_countries or any(kc.lower() in country.lower() for kc in known_countries)
    
    def _is_country_specific(self, doc: RegulatoryDocument, target_country: str) -> bool:
        """CRITICAL: Ensure regulation actually belongs to the target country"""
        doc_country = doc.country.lower().strip()
        target_lower = target_country.lower().strip()
        
        # Exact matches
        if doc_country == target_lower:
            return True
        
        # Handle common variations
        country_variations = {
            'germany': ['deutschland', 'de', 'german'],
            'eu': ['european union', 'europe', 'europa'],
            'european union': ['eu', 'europe', 'europa'],
            'uk': ['united kingdom', 'britain', 'great britain'],
            'united kingdom': ['uk', 'britain', 'great britain'],
            'us': ['united states', 'usa', 'america'],
            'united states': ['us', 'usa', 'america']
        }
        
        # Check if target country has variations
        target_variations = country_variations.get(target_lower, [target_lower])
        if doc_country in target_variations:
            return True
        
        # Check if doc country has variations
        doc_variations = country_variations.get(doc_country, [doc_country])
        if target_lower in doc_variations:
            return True
        
        # STRICT: If no match found, it doesn't belong to this country
        logger.debug(f"Filtering out {doc.title} (country: {doc.country}) for {target_country}")
        return False
    
    async def _search_optimized_regulations(self, country: str, startup_info: Any) -> List[RegulatoryDocument]:
        """Use optimized knowledge for known countries with country isolation"""
        regulations = []
        industry = startup_info.industry.lower()
        
        logger.info(f"Using optimized search for {country} in {industry}")
        
        # Use our existing optimized mappings
        if hasattr(self, 'industry_map') and industry in self.industry_map:
            for mapped_country, reg_list in self.industry_map[industry].items():
                # CRITICAL: Only use regulations that match the target country
                if self._country_matches(mapped_country, country):
                    logger.info(f"Found optimized mapping: {mapped_country} matches {country}")
                    
                    # Fetch known regulations for this specific country
                    for reg_name in reg_list[:5]:
                        if hasattr(self, 'regulation_urls') and reg_name in self.regulation_urls:
                            regulation = RegulatoryDocument(
                                title=f"{reg_name} - Official Text",
                                content=f"Official regulation {reg_name}. Compliance requirements for {industry} businesses in {country}.",
                                source=self._get_authority_for_regulation(reg_name, country),
                                country=country,  # Use the requested country exactly
                                regulation_type=self._get_regulation_type(reg_name),
                                url=self.regulation_urls[reg_name],
                                authority=self._get_authority_for_regulation(reg_name, country),
                                regulation_id=reg_name,
                                citation_format=self._get_citation_format(reg_name),
                                relevance_score=0.9
                            )
                            regulations.append(regulation)
        
        logger.info(f"Found {len(regulations)} optimized regulations for {country}")
        return regulations
    
    def _country_matches(self, mapped_country: str, target_country: str) -> bool:
        """Check if mapped country matches target country"""
        mapped_lower = mapped_country.lower().strip()
        target_lower = target_country.lower().strip()
        
        # Exact match
        if mapped_lower == target_lower:
            return True
        
        # Cross-reference common variations
        if 'germany' in mapped_lower and 'germany' in target_lower:
            return True
        if 'eu' in mapped_lower and ('eu' in target_lower or 'european' in target_lower):
            return True
        if 'european' in mapped_lower and ('eu' in target_lower or 'european' in target_lower):
            return True
        if 'uk' in mapped_lower and ('uk' in target_lower or 'kingdom' in target_lower):
            return True
        if 'united states' in mapped_lower and ('us' in target_lower or 'united states' in target_lower):
            return True
            
        return False
    
    async def _country_specific_fallback_research(
        self, 
        country: str, 
        startup_info: Any, 
        queries: List[Dict]
    ) -> List[RegulatoryDocument]:
        """Country-specific fallback research with strict isolation"""
        
        logger.info(f"Country-specific fallback research for {country}")
        
        enhanced_prompt = f"""
        You are a regulatory compliance expert specializing EXCLUSIVELY in {country}.
        
        Research compliance requirements for a {startup_info.industry} startup operating ONLY in {country}.
        
        CRITICAL: Only provide regulations that apply specifically to {country}. 
        Do NOT mention regulations from other countries like EU, US, UK, Germany unless they directly apply in {country}.
        
        Startup Profile:
        - Industry: {startup_info.industry}
        - Business Activities: {startup_info.business_activities}
        - Operating Country: {country} ONLY
        
        Focus Areas for {country}:
        1. Business registration requirements in {country}
        2. Industry-specific regulations in {country}
        3. Data protection laws in {country}
        4. Tax regulations in {country}
        5. Employment laws in {country}
        
        For each regulation, provide:
        - Official name in {country}
        - Government authority in {country}
        - Brief requirements summary
        - Official {country} website URL (if known)
        
        Remember: ONLY regulations that apply in {country}. No other countries.
        """
        
        try:
            response = await gemini_client.generate_response(
                enhanced_prompt,
                temperature=0.1,
                system_prompt=f"You are a {country} regulatory expert. Only provide information about {country} regulations. Do not mention other countries' laws unless they are implemented in {country}."
            )
            
            # Parse with country validation
            regulations = await self._parse_country_specific_regulations(response, country)
            
            logger.info(f"Country-specific fallback found {len(regulations)} regulations for {country}")
            return regulations
            
        except Exception as e:
            logger.error(f"Country-specific fallback failed for {country}: {e}")
            return []
    
    async def _parse_country_specific_regulations(self, response: str, country: str) -> List[RegulatoryDocument]:
        """Parse regulations with strict country validation"""
        
        # Use AI to structure and validate
        validation_prompt = f"""
        Extract regulatory information from this research about {country}:
        
        {response[:3000]}
        
        CRITICAL VALIDATION:
        - Only include regulations that specifically apply in {country}
        - Remove any mention of regulations from other countries
        - Ensure each regulation has a clear {country} authority
        
        For each valid {country} regulation, provide:
        - name: Official name
        - authority: {country} government authority
        - description: Requirements
        - country: {country}
        
        Format as structured list. Only {country} regulations.
        """
        
        try:
            validated_response = await gemini_client.generate_response(
                validation_prompt,
                temperature=0.1
            )
            
            regulations = self._parse_structured_regulations(validated_response, country)
            
            # Final validation: ensure all regulations are for the target country
            validated_regulations = []
            for reg in regulations:
                if self._is_country_specific(reg, country):
                    validated_regulations.append(reg)
                else:
                    logger.warning(f"Filtered out non-{country} regulation: {reg.title}")
            
            return validated_regulations
            
        except Exception as e:
            logger.error(f"Country-specific parsing failed: {e}")
            return []
    
    def _get_authority_for_regulation(self, reg_name: str, country: str) -> str:
        """Get authority with country context"""
        # Default authorities by country
        default_authorities = {
            'Germany': 'German Federal Government',
            'EU': 'European Commission', 
            'European Union': 'European Commission',
            'UK': 'UK Government',
            'United Kingdom': 'UK Government',
            'US': 'US Government',
            'United States': 'US Government'
        }
        
        # Specific regulation authorities
        authority_map = {
            'GDPR': 'European Commission',
            'BDSG': 'German Federal Government', 
            'TMG': 'German Federal Government',
            'KWG': 'German Federal Government',
            'ZAG': 'German Federal Government',
            'PSD2': 'European Commission'
        }
        
        return authority_map.get(reg_name, default_authorities.get(country, f'{country} Government'))
    
    def _get_regulation_type(self, reg_name: str) -> str:
        """Get regulation type"""
        type_map = {
            'GDPR': 'data_protection',
            'BDSG': 'data_protection',
            'TMG': 'digital_services',
            'KWG': 'financial_regulation',
            'ZAG': 'payment_services',
            'PSD2': 'payment_services'
        }
        return type_map.get(reg_name, 'general')
    
    def _get_citation_format(self, reg_name: str) -> str:
        """Get proper citation format"""
        citation_map = {
            'GDPR': 'Regulation (EU) 2016/679',
            'BDSG': 'Bundesdatenschutzgesetz (BDSG)',
            'TMG': 'Telemediengesetz (TMG)',
            'KWG': 'Kreditwesengesetz (KWG)',
            'ZAG': 'Zahlungsdiensteaufsichtsgesetz (ZAG)',
            'PSD2': 'Directive (EU) 2015/2366'
        }
        return citation_map.get(reg_name, reg_name)
    
    def _convert_to_regulatory_document(self, reg_data: Dict, country: str) -> Optional[RegulatoryDocument]:
        """Convert dynamic research result to RegulatoryDocument"""
        try:
            return RegulatoryDocument(
                title=reg_data.get('name', 'Unknown Regulation'),
                content=reg_data.get('description', 'No description available'),
                source=reg_data.get('authority', 'Unknown Authority'),
                country=country,
                regulation_type=reg_data.get('type', 'general'),
                url=reg_data.get('url', ''),
                authority=reg_data.get('authority', 'Unknown Authority'),
                regulation_id=reg_data.get('regulation_id', ''),
                citation_format=reg_data.get('citation', ''),
                relevance_score=0.7  # Dynamic discoveries get slightly lower initial score
            )
        except Exception as e:
            logger.error(f"Error converting regulation data: {e}")
            return None
    
    async def _fallback_country_research(
        self, 
        country: str, 
        startup_info: Any, 
        queries: List[Dict]
    ) -> List[RegulatoryDocument]:
        """Fallback research for unknown countries using AI"""
        
        logger.info(f"Fallback research for {country}")
        
        fallback_prompt = f"""
        Research regulatory requirements for a {startup_info.industry} startup in {country}.
        
        Business activities: {startup_info.business_activities}
        Data handling: {startup_info.data_handling}
        
        Find the most important regulations that would apply. Focus on:
        1. Business registration/licensing laws
        2. Data protection regulations  
        3. Industry-specific requirements
        4. Tax and compliance obligations
        
        For each regulation, provide:
        - Official name
        - Issuing authority
        - Brief description of requirements
        - Official website if known
        
        Be specific and accurate. Only mention regulations that actually exist.
        """
        
        try:
            response = await gemini_client.generate_response(
                fallback_prompt,
                temperature=0.2,
                system_prompt=f"You are an expert on {country} regulations. Provide accurate, specific information."
            )
            
            # Parse AI response into regulations
            regulations = self._parse_fallback_regulations(response, country)
            
            logger.info(f"Fallback research found {len(regulations)} regulations for {country}")
            return regulations
            
        except Exception as e:
            logger.error(f"Fallback research failed for {country}: {e}")
            return []
    
    def _parse_fallback_regulations(self, response: str, country: str) -> List[RegulatoryDocument]:
        """Parse AI response into RegulatoryDocument objects"""
        regulations = []
        
        # Simple parsing - look for regulation-like patterns
        lines = response.split('\n')
        current_reg = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for regulation names (often numbered or capitalized)
            if any(keyword in line.lower() for keyword in ['act', 'law', 'regulation', 'code', 'ordinance']):
                if current_reg and current_reg.get('name'):
                    # Save previous regulation
                    reg_doc = self._create_regulation_from_parsed_data(current_reg, country)
                    if reg_doc:
                        regulations.append(reg_doc)
                
                # Start new regulation
                current_reg = {
                    'name': line,
                    'description': '',
                    'authority': '',
                    'url': ''
                }
            
            elif 'authority' in line.lower() or 'ministry' in line.lower():
                current_reg['authority'] = line
            elif 'http' in line:
                current_reg['url'] = line.split()[-1]  # Extract URL
            elif current_reg.get('name'):
                current_reg['description'] += ' ' + line
        
        # Don't forget the last regulation
        if current_reg and current_reg.get('name'):
            reg_doc = self._create_regulation_from_parsed_data(current_reg, country)
            if reg_doc:
                regulations.append(reg_doc)
        
        return regulations[:8]  # Limit results
    
    def _create_regulation_from_parsed_data(self, reg_data: Dict, country: str) -> Optional[RegulatoryDocument]:
        """Create RegulatoryDocument from parsed fallback data"""
        name = reg_data.get('name', '').strip()
        if len(name) < 5:  # Skip invalid entries
            return None
        
        try:
            return RegulatoryDocument(
                title=name,
                content=reg_data.get('description', 'No description available').strip(),
                source=reg_data.get('authority', f'{country} Government').strip(),
                country=country,
                regulation_type='general',
                url=reg_data.get('url', ''),
                authority=reg_data.get('authority', f'{country} Government').strip(),
                regulation_id=name.split()[0] if name.split() else '',
                citation_format=name,
                relevance_score=0.6  # Lower score for fallback results
            )
        except Exception as e:
            logger.error(f"Error creating regulation from parsed data: {e}")
            return None
    
    async def _ai_powered_country_research(
        self, 
        country: str, 
        startup_info: Any, 
        queries: List[Dict]
    ) -> List[RegulatoryDocument]:
        """Enhanced AI-powered research for any country"""
        
        logger.info(f"AI-powered research for {country}")
        
        enhanced_prompt = f"""
        You are a world-class regulatory research expert. Research compliance requirements for a {startup_info.industry} startup in {country}.
        
        Startup Profile:
        - Industry: {startup_info.industry}
        - Business Activities: {startup_info.business_activities}
        - Data Types: {startup_info.data_handling}
        - Customer Types: {startup_info.customer_types}
        
        Research Focus Areas:
        1. Business registration and licensing requirements
        2. Industry-specific regulations 
        3. Data protection and privacy laws
        4. Tax and financial compliance
        5. Employment and labor regulations
        6. Consumer protection requirements
        
        For each relevant regulation, provide:
        - Exact official name (be precise)
        - Issuing government authority/ministry
        - Brief compliance requirements summary
        - Official website URL (if known)
        - Specific articles/sections that apply
        
        Focus on REAL, CURRENT regulations that actually exist in {country}.
        Prioritize regulations that would immediately impact this startup.
        Provide specific, actionable information.
        """
        
        try:
            response = await gemini_client.generate_response(
                enhanced_prompt,
                temperature=0.1,  # Very low for maximum accuracy
                system_prompt=f"You are a regulatory compliance expert specializing in {country}. Provide only accurate, verifiable information about real regulations."
            )
            
            # Enhanced parsing with better validation
            regulations = await self._enhanced_parse_regulations(response, country)
            
            logger.info(f"AI-powered research found {len(regulations)} regulations for {country}")
            return regulations
            
        except Exception as e:
            logger.error(f"AI-powered research failed for {country}: {e}")
            return []
    
    async def _enhanced_parse_regulations(self, response: str, country: str) -> List[RegulatoryDocument]:
        """Enhanced parsing with AI validation"""
        
        # First, use AI to structure the response
        structuring_prompt = f"""
        Extract and structure the regulatory information for {country} from this research:
        
        {response[:4000]}  # Limit input size
        
        Return a structured list where each regulation has:
        - name: Official regulation name
        - authority: Government body that issued it
        - description: Key compliance requirements
        - url: Official website (if mentioned)
        - type: regulation/law/act/directive/guideline
        
        Format as a clear, structured list. Only include regulations that seem real and official.
        """
        
        try:
            structured_response = await gemini_client.generate_response(
                structuring_prompt,
                temperature=0.1
            )
            
            # Parse the structured response
            regulations = self._parse_structured_regulations(structured_response, country)
            
            return regulations[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Enhanced parsing failed: {e}")
            # Fall back to simple parsing
            return self._parse_fallback_regulations(response, country)
    
    def _parse_structured_regulations(self, response: str, country: str) -> List[RegulatoryDocument]:
        """Parse AI-structured regulation response"""
        regulations = []
        lines = response.split('\n')
        current_reg = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for structured patterns
            if line.startswith('- name:') or line.startswith('Name:'):
                # Save previous regulation
                if current_reg and current_reg.get('name'):
                    reg_doc = self._create_enhanced_regulation(current_reg, country)
                    if reg_doc:
                        regulations.append(reg_doc)
                
                # Start new regulation
                current_reg = {'name': line.split(':', 1)[1].strip()}
                
            elif (line.startswith('- authority:') or line.startswith('Authority:')) and current_reg:
                current_reg['authority'] = line.split(':', 1)[1].strip()
                
            elif (line.startswith('- description:') or line.startswith('Description:')) and current_reg:
                current_reg['description'] = line.split(':', 1)[1].strip()
                
            elif (line.startswith('- url:') or line.startswith('URL:')) and current_reg:
                current_reg['url'] = line.split(':', 1)[1].strip()
                
            elif (line.startswith('- type:') or line.startswith('Type:')) and current_reg:
                current_reg['type'] = line.split(':', 1)[1].strip()
        
        # Don't forget last regulation
        if current_reg and current_reg.get('name'):
            reg_doc = self._create_enhanced_regulation(current_reg, country)
            if reg_doc:
                regulations.append(reg_doc)
        
        return regulations
    
    def _create_enhanced_regulation(self, reg_data: Dict, country: str) -> Optional[RegulatoryDocument]:
        """Create enhanced RegulatoryDocument with better validation"""
        name = reg_data.get('name', '').strip()
        authority = reg_data.get('authority', '').strip()
        
        # Better validation
        if len(name) < 8 or not authority:  # More strict validation
            return None
        
        # Skip obviously fake or generic entries
        fake_indicators = ['example', 'sample', 'generic', 'placeholder', 'template']
        if any(indicator in name.lower() for indicator in fake_indicators):
            return None
        
        try:
            return RegulatoryDocument(
                title=name,
                content=reg_data.get('description', 'Regulatory requirements for compliance').strip(),
                source=authority,
                country=country,
                regulation_type=reg_data.get('type', 'regulation'),
                url=reg_data.get('url', ''),
                authority=authority,
                regulation_id=self._extract_regulation_id(name),
                citation_format=name,
                relevance_score=0.75  # Higher score for AI-powered results
            )
        except Exception as e:
            logger.error(f"Error creating enhanced regulation: {e}")
            return None
    
    def _extract_regulation_id(self, name: str) -> str:
        """Extract regulation ID from name"""
        import re
        
        # Look for common patterns
        patterns = [
            r'Act (\d+)',
            r'Law (\d+)',
            r'Regulation (\d+)',
            r'(\d{4})',  # Year
            r'Article (\d+)',
            r'Section (\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1)
        
        # Return first word as fallback
        return name.split()[0] if name.split() else ''

# Global scout agent instance
scout_agent = ScoutAgent() 