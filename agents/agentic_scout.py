"""
Agentic Regulation Scout Agent
Uses multi-step reasoning and web scraping to discover real regulatory requirements
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup
from integrations.gemini_client import gemini_client
import json
import re

class RegulationSource(BaseModel):
    """Official regulation source"""
    name: str
    base_url: str
    country: str
    authority: str
    search_patterns: List[str]
    api_endpoint: Optional[str] = None

class ResearchPlan(BaseModel):
    """Agentic research plan"""
    industry: str
    countries: List[str]
    research_steps: List[Dict[str, Any]]
    priority_areas: List[str]
    expected_regulations: List[str]

class AgenticScoutAgent:
    """Advanced agentic agent for autonomous regulation discovery"""
    
    def __init__(self):
        self.agent_name = "AgenticScoutAgent"
        self.regulation_sources = self._initialize_sources()
        logger.info(f"{self.agent_name} initialized with {len(self.regulation_sources)} official sources")
    
    def _initialize_sources(self) -> Dict[str, RegulationSource]:
        """Initialize official regulatory sources"""
        return {
            "eur_lex": RegulationSource(
                name="EUR-Lex",
                base_url="https://eur-lex.europa.eu",
                country="EU",
                authority="European Commission",
                search_patterns=[
                    "/search.html?qid=&text={query}&scope=EURLEX&type=quick&lang=en",
                    "/eli/reg/*/OJ"  # Official Journal pattern
                ],
                api_endpoint="https://publications.europa.eu/webapi/rdf/sparql"
            ),
            "german_laws": RegulationSource(
                name="Gesetze im Internet",
                base_url="https://www.gesetze-im-internet.de",
                country="Germany", 
                authority="German Federal Government",
                search_patterns=[
                    "/suche/index.html?query={query}",
                    "/{law_code}/"  # Direct law access
                ]
            ),
            "bafin": RegulationSource(
                name="BaFin Regulations",
                base_url="https://www.bafin.de",
                country="Germany",
                authority="Federal Financial Supervisory Authority",
                search_patterns=[
                    "/EN/Supervision/{sector}/",
                    "/SharedDocs/Veroeffentlichungen/"
                ]
            ),
            "bsi": RegulationSource(
                name="BSI Guidelines",
                base_url="https://www.bsi.bund.de",
                country="Germany", 
                authority="Federal Office for Information Security",
                search_patterns=[
                    "/EN/Topics/{topic}/",
                    "/SharedDocs/Downloads/"
                ]
            )
        }
    
    async def create_research_plan(self, startup_info: Any, queries: List[Dict]) -> ResearchPlan:
        """Create an agentic research plan"""
        logger.info(f"{self.agent_name}: Creating agentic research plan")
        
        planning_prompt = f"""
        You are a regulatory research AI agent. Create a comprehensive research plan to find REAL regulations 
        for this startup:
        
        Industry: {startup_info.industry}
        Countries: {startup_info.target_countries}
        Activities: {startup_info.business_activities}
        Data Handling: {startup_info.data_handling}
        
        Create a step-by-step research plan that:
        1. Identifies the most likely regulations that apply
        2. Prioritizes research areas by risk and importance
        3. Plans a logical sequence of discovery steps
        4. Suggests specific search terms and sources
        
        Return a JSON plan with:
        - research_steps: [{{step: 1, action: "search_gdpr_articles", source: "eur_lex", query: "data protection health", expected_findings: ["Article 9", "Article 32"]}}]
        - priority_areas: ["data protection", "licensing", "reporting"]  
        - expected_regulations: ["GDPR", "BDSG", "MDR", "PSD2"]
        """
        
        try:
            response = await gemini_client.generate_response(
                planning_prompt,
                temperature=0.3,
                system_prompt="You are a regulatory research expert. Create precise, actionable research plans."
            )
            
            # Parse the research plan
            plan_data = self._parse_research_plan(response)
            
            research_plan = ResearchPlan(
                industry=startup_info.industry,
                countries=startup_info.target_countries,
                research_steps=plan_data.get('research_steps', []),
                priority_areas=plan_data.get('priority_areas', []),
                expected_regulations=plan_data.get('expected_regulations', [])
            )
            
            logger.info(f"{self.agent_name}: Created plan with {len(research_plan.research_steps)} steps")
            return research_plan
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error creating research plan: {e}")
            # Fallback plan
            return self._create_fallback_plan(startup_info)
    
    async def execute_research_plan(self, plan: ResearchPlan) -> List[Dict]:
        """Execute the agentic research plan"""
        logger.info(f"{self.agent_name}: Executing {len(plan.research_steps)} research steps")
        
        discovered_regulations = []
        research_context = {}  # Maintain context between steps
        
        async with aiohttp.ClientSession() as session:
            for step_idx, step in enumerate(plan.research_steps):
                logger.info(f"{self.agent_name}: Step {step_idx + 1}: {step.get('action', 'Unknown')}")
                
                try:
                    # Execute research step
                    step_results = await self._execute_research_step(
                        session, step, research_context, plan
                    )
                    
                    if step_results:
                        discovered_regulations.extend(step_results)
                        # Update context for next steps
                        research_context[f"step_{step_idx}"] = step_results
                        
                        # Agentic decision: Should we explore deeper?
                        if await self._should_explore_deeper(step_results, plan):
                            deeper_results = await self._explore_related_regulations(
                                session, step_results, plan
                            )
                            discovered_regulations.extend(deeper_results)
                    
                    # Brief pause between requests to be respectful
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"{self.agent_name}: Error in step {step_idx + 1}: {e}")
                    continue
        
        # Post-process and validate findings
        validated_regulations = await self._validate_regulations(discovered_regulations)
        
        logger.info(f"{self.agent_name}: Discovered {len(validated_regulations)} validated regulations")
        return validated_regulations
    
    async def _execute_research_step(
        self, 
        session: aiohttp.ClientSession, 
        step: Dict, 
        context: Dict,
        plan: ResearchPlan
    ) -> List[Dict]:
        """Execute a single research step"""
        
        action = step.get('action')
        source_name = step.get('source')
        query = step.get('query')
        
        if source_name not in self.regulation_sources:
            logger.warning(f"Unknown source: {source_name}")
            return []
        
        source = self.regulation_sources[source_name]
        
        # Different execution strategies based on action type
        if action == "search_eur_lex":
            return await self._search_eur_lex(session, source, query, step)
        elif action == "search_german_laws":
            return await self._search_german_laws(session, source, query, step)
        elif action == "scrape_bafin_guidance":
            return await self._scrape_bafin_guidance(session, source, query, step)
        elif action == "discover_related":
            return await self._discover_related_regulations(session, context, step)
        else:
            logger.warning(f"Unknown action: {action}")
            return []
    
    async def _search_eur_lex(
        self, 
        session: aiohttp.ClientSession, 
        source: RegulationSource, 
        query: str,
        step: Dict
    ) -> List[Dict]:
        """Search EUR-Lex for EU regulations"""
        try:
            search_url = f"{source.base_url}/search.html?qid=&text={query}&scope=EURLEX&type=quick&lang=en"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    regulations = []
                    # Parse EUR-Lex search results
                    for result in soup.find_all('div', class_='SearchResult')[:5]:  # Top 5 results
                        title_elem = result.find('a', class_='title')
                        if title_elem:
                            title = title_elem.get_text().strip()
                            url = title_elem.get('href')
                            if url and url.startswith('/'):
                                url = source.base_url + url
                            
                            # Extract regulation details
                            regulation = {
                                'title': title,
                                'url': url,
                                'source': source.name,
                                'country': source.country,
                                'authority': source.authority,
                                'regulation_type': self._classify_regulation_type(title),
                                'content': await self._extract_regulation_content(session, url),
                                'regulation_id': self._extract_regulation_id(title)
                            }
                            regulations.append(regulation)
                    
                    return regulations
                else:
                    logger.warning(f"EUR-Lex search failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching EUR-Lex: {e}")
            return []
    
    async def _search_german_laws(
        self,
        session: aiohttp.ClientSession,
        source: RegulationSource, 
        query: str,
        step: Dict
    ) -> List[Dict]:
        """Search German federal laws"""
        try:
            # Known German laws for different industries
            german_laws = {
                'healthcare': ['BDSG', 'TMG', 'DSGVO-Anpassungs-und-Umsetzungsgesetz'],
                'fintech': ['KWG', 'ZAG', 'WpHG', 'BDSG'],
                'technology': ['TMG', 'BDSG', 'TKG'],
                'general': ['BDSG', 'TMG', 'HGB']
            }
            
            industry = step.get('industry', 'general').lower()
            relevant_laws = german_laws.get(industry, german_laws['general'])
            
            regulations = []
            for law_code in relevant_laws:
                law_url = f"{source.base_url}/{law_code.lower()}/"
                
                try:
                    async with session.get(law_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            content = await self._parse_german_law(html, law_code)
                            
                            regulation = {
                                'title': f"German {law_code}",
                                'url': law_url,
                                'source': source.name,
                                'country': source.country,
                                'authority': source.authority,
                                'regulation_type': 'federal_law',
                                'content': content,
                                'regulation_id': law_code
                            }
                            regulations.append(regulation)
                except:
                    continue  # Skip if law doesn't exist
                    
            return regulations
            
        except Exception as e:
            logger.error(f"Error searching German laws: {e}")
            return []
    
    async def _should_explore_deeper(self, results: List[Dict], plan: ResearchPlan) -> bool:
        """Agentic decision: Should we explore related regulations?"""
        if not results:
            return False
        
        # Use AI to decide if we should go deeper
        decision_prompt = f"""
        Based on these regulation findings, should we explore related regulations?
        
        Found regulations: {[r.get('title', 'Unknown') for r in results[:3]]}
        Industry: {plan.industry}
        Priority areas: {plan.priority_areas}
        
        Return 'YES' if we should explore related regulations, 'NO' if current findings are sufficient.
        Consider: regulatory complexity, cross-references, implementation requirements.
        """
        
        try:
            response = await gemini_client.generate_response(decision_prompt, temperature=0.2)
            return 'YES' in response.upper()
        except:
            return len(results) < 3  # Fallback: explore if we have few results
    
    def _parse_research_plan(self, response: str) -> Dict:
        """Parse AI response into research plan"""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._extract_plan_from_text(response)
        except:
            return {}
    
    def _create_fallback_plan(self, startup_info: Any) -> ResearchPlan:
        """Create a fallback research plan"""
        return ResearchPlan(
            industry=startup_info.industry,
            countries=startup_info.target_countries,
            research_steps=[
                {
                    "step": 1,
                    "action": "search_eur_lex",
                    "source": "eur_lex", 
                    "query": f"{startup_info.industry} data protection",
                    "expected_findings": ["GDPR"]
                },
                {
                    "step": 2,
                    "action": "search_german_laws",
                    "source": "german_laws",
                    "query": f"{startup_info.industry} compliance",
                    "expected_findings": ["BDSG"]
                }
            ],
            priority_areas=["data protection", "business licensing"],
            expected_regulations=["GDPR", "BDSG"]
        )
    
    def _classify_regulation_type(self, title: str) -> str:
        """Classify regulation type from title"""
        title_lower = title.lower()
        
        if 'regulation' in title_lower and 'eu' in title_lower:
            return 'eu_regulation'
        elif 'directive' in title_lower:
            return 'eu_directive'
        elif 'data protection' in title_lower or 'gdpr' in title_lower:
            return 'data_protection'
        elif 'financial' in title_lower or 'payment' in title_lower:
            return 'financial_regulation'
        else:
            return 'general'
    
    def _extract_regulation_id(self, title: str) -> Optional[str]:
        """Extract regulation ID from title"""
        import re
        
        # EU regulation patterns
        eu_pattern = r'Regulation \(EU\) (\d+/\d+)'
        match = re.search(eu_pattern, title)
        if match:
            return f"EU Reg {match.group(1)}"
        
        # Article patterns
        article_pattern = r'Article (\d+)'
        match = re.search(article_pattern, title)
        if match:
            return f"Art. {match.group(1)}"
        
        return None

# Global agentic scout instance
agentic_scout = AgenticScoutAgent() 