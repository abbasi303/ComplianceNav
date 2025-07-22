"""
Regional Regulatory Agent - Smart Country-Specific Compliance Research
Pluggable architecture: Enhanced coverage for supported countries, fallback for others
"""

import asyncio
import importlib
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from pydantic import BaseModel
from loguru import logger
from integrations.gemini_client import gemini_client
from core.data_models import RegulatoryDocument

class CountryModule(ABC):
    """Base class for country-specific regulatory modules"""
    
    def __init__(self, country_name: str):
        self.country_name = country_name
        self.authorities = {}
        self.regulation_patterns = {}
        self.search_strategies = {}
    
    @abstractmethod
    async def research_regulations(self, industry: str, business_activities: List[str], startup_info: Any) -> List[RegulatoryDocument]:
        """Research regulations specific to this country"""
        pass
    
    @abstractmethod
    def get_authority_mapping(self) -> Dict[str, str]:
        """Get mapping of regulation types to authorities"""
        pass
    
    @abstractmethod
    def get_priority_regulations(self, industry: str) -> List[str]:
        """Get priority regulations for specific industry in this country"""
        pass

class RegionalRegulatoryAgent:
    """
    Smart Regional Agent with Country Module Architecture
    - Loads country-specific modules for enhanced coverage
    - Falls back to generic research for unsupported countries  
    - Easy to expand without system redesign
    """
    
    def __init__(self):
        self.agent_name = "RegionalRegulatoryAgent"
        self.country_modules: Dict[str, CountryModule] = {}
        self.supported_countries = []
        self._load_available_modules()
        
        logger.info(f"{self.agent_name}: Initialized with {len(self.supported_countries)} country modules")
    
    def _load_available_modules(self):
        """Dynamically load available country modules"""
        try:
            # Try to load Pakistan module (our first implementation)
            from agents.country_modules.pakistan_module import PakistanRegulatoryModule
            self.country_modules['pakistan'] = PakistanRegulatoryModule()
            self.supported_countries.append('Pakistan')
            logger.info(f"{self.agent_name}: Loaded Pakistan regulatory module")
        except ImportError:
            logger.debug("Pakistan module not yet available")
        
        # Try to load other modules as they become available
        # This is where we'd add: USA, Germany, UK, etc.
        try:
            from agents.country_modules.usa_module import USARegulatoryModule
            self.country_modules['usa'] = USARegulatoryModule()
            self.country_modules['united states'] = self.country_modules['usa']  # Alias
            self.supported_countries.append('USA')
            logger.info(f"{self.agent_name}: Loaded USA regulatory module")
        except ImportError:
            logger.debug("USA module not yet available")
    
    async def research_country_regulations(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str],
        startup_info: Any
    ) -> List[RegulatoryDocument]:
        """
        Research regulations for a specific country
        Uses country module if available, falls back to generic research
        """
        
        country_key = country.lower().strip()
        
        # Step 1: Check if we have a specialized module for this country
        if country_key in self.country_modules:
            logger.info(f"{self.agent_name}: Using specialized module for {country}")
            try:
                # Use country-specific module for enhanced results
                regulations = await self.country_modules[country_key].research_regulations(
                    industry, business_activities, startup_info
                )
                
                # Add country-specific metadata
                for reg in regulations:
                    reg.regional_module = True
                    reg.coverage_quality = "enhanced"
                    reg.module_version = getattr(self.country_modules[country_key], 'version', '1.0')
                
                logger.info(f"{self.agent_name}: Enhanced module returned {len(regulations)} regulations for {country}")
                return regulations
                
            except Exception as e:
                logger.error(f"Error in {country} module: {e}. Falling back to generic research.")
        
        else:
            logger.info(f"{self.agent_name}: No specialized module for {country}, using dynamic research")
        
        # Step 2: Fallback to enhanced generic research
        fallback_regulations = await self._dynamic_country_research(
            country, industry, business_activities, startup_info
        )
        
        # Mark as fallback results
        for reg in fallback_regulations:
            reg.regional_module = False
            reg.coverage_quality = "standard"
            reg.research_method = "dynamic_fallback"
        
        logger.info(f"{self.agent_name}: Dynamic research returned {len(fallback_regulations)} regulations for {country}")
        return fallback_regulations
    
    async def _dynamic_country_research(
        self,
        country: str,
        industry: str, 
        business_activities: List[str],
        startup_info: Any
    ) -> List[RegulatoryDocument]:
        """Enhanced dynamic research for countries without specific modules"""
        
        # Create targeted research prompt
        research_prompt = f"""
        Research regulatory compliance requirements for a {industry} startup in {country}.
        
        Business Profile:
        - Industry: {industry}
        - Activities: {', '.join(business_activities)}
        - Target Market: {country}
        - Stage: Early-stage startup
        
        Focus Areas:
        1. Business Registration & Licensing
        2. Industry-Specific Regulations  
        3. Tax & Financial Compliance
        4. Data Protection & Privacy
        5. Employment & Labor Law
        6. Import/Export Requirements (if applicable)
        
        For each relevant regulation, provide:
        - Official name and regulation number
        - Issuing authority/ministry
        - Key compliance requirements
        - Implementation deadlines
        - Penalties for non-compliance
        
        Focus on REAL, CURRENT regulations specific to {country}.
        Be specific about government authorities and official processes.
        """
        
        try:
            # Get AI-powered research
            response = await gemini_client.generate_response(
                research_prompt,
                temperature=0.1,  # Low temperature for accuracy
                system_prompt=f"You are a regulatory expert specializing in {country}. Provide accurate, actionable information about real regulations."
            )
            
            # Parse response into regulatory documents
            regulations = await self._parse_dynamic_research_response(response, country)
            
            return regulations
            
        except Exception as e:
            logger.error(f"Dynamic research failed for {country}: {e}")
            return []
    
    async def _parse_dynamic_research_response(self, response: str, country: str) -> List[RegulatoryDocument]:
        """Parse AI response into structured regulatory documents"""
        
        regulations = []
        current_regulation = None
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for regulation names/titles
            if any(keyword in line.lower() for keyword in ['act', 'law', 'regulation', 'code', 'ordinance', 'decree']):
                # Save previous regulation if exists
                if current_regulation and current_regulation.get('name'):
                    reg_doc = self._create_regulation_from_dynamic_data(current_regulation, country)
                    if reg_doc:
                        regulations.append(reg_doc)
                
                # Start new regulation
                current_regulation = {
                    'name': line,
                    'authority': '',
                    'description': '',
                    'requirements': [],
                    'penalties': ''
                }
            
            elif current_regulation:
                # Add details to current regulation
                if 'authority:' in line.lower() or 'ministry:' in line.lower():
                    current_regulation['authority'] = line.split(':', 1)[1].strip()
                elif 'requirement' in line.lower():
                    current_regulation['requirements'].append(line)
                elif 'penalty' in line.lower() or 'fine' in line.lower():
                    current_regulation['penalties'] = line
                else:
                    # Add to description
                    if current_regulation['description']:
                        current_regulation['description'] += ' ' + line
                    else:
                        current_regulation['description'] = line
        
        # Don't forget the last regulation
        if current_regulation and current_regulation.get('name'):
            reg_doc = self._create_regulation_from_dynamic_data(current_regulation, country)
            if reg_doc:
                regulations.append(reg_doc)
        
        return regulations[:10]  # Limit to top 10 most relevant
    
    def _create_regulation_from_dynamic_data(self, reg_data: Dict, country: str) -> Optional[RegulatoryDocument]:
        """Convert parsed regulation data to RegulatoryDocument"""
        
        name = reg_data.get('name', '').strip()
        if len(name) < 5:  # Skip invalid entries
            return None
        
        try:
            # Combine description and requirements
            content_parts = []
            if reg_data.get('description'):
                content_parts.append(reg_data['description'])
            if reg_data.get('requirements'):
                content_parts.append("Requirements: " + '; '.join(reg_data['requirements']))
            if reg_data.get('penalties'):
                content_parts.append("Penalties: " + reg_data['penalties'])
            
            content = '\n\n'.join(content_parts) if content_parts else "Regulation details available from official sources."
            
            return RegulatoryDocument(
                title=name,
                content=content,
                source=reg_data.get('authority', f'{country} Government').strip(),
                country=country,
                regulation_type='general',
                authority=reg_data.get('authority', f'{country} Government').strip(),
                regulation_id=self._extract_regulation_id(name),
                citation_format=name,
                relevance_score=0.7  # Standard score for dynamic research
            )
            
        except Exception as e:
            logger.error(f"Error creating regulation document: {e}")
            return None
    
    def _extract_regulation_id(self, regulation_name: str) -> str:
        """Extract regulation ID/number from name"""
        import re
        
        # Look for common patterns: Act 2020, Law No. 123, Regulation 456/2021
        patterns = [
            r'\d{4}',  # Year
            r'No\.\s*\d+',  # No. 123
            r'\d+/\d+',  # 456/2021
            r'Art\.\s*\d+',  # Art. 32
        ]
        
        for pattern in patterns:
            match = re.search(pattern, regulation_name)
            if match:
                return match.group(0)
        
        # Fallback: return first few words
        words = regulation_name.split()
        return ' '.join(words[:2]) if len(words) >= 2 else regulation_name
    
    def get_supported_countries(self) -> List[str]:
        """Get list of countries with enhanced module support"""
        return self.supported_countries.copy()
    
    def has_enhanced_support(self, country: str) -> bool:
        """Check if country has enhanced module support"""
        return country.lower().strip() in self.country_modules
    
    async def get_country_authorities(self, country: str) -> Dict[str, str]:
        """Get regulatory authorities for a country"""
        country_key = country.lower().strip()
        
        if country_key in self.country_modules:
            return self.country_modules[country_key].get_authority_mapping()
        else:
            # Return generic mapping for unsupported countries
            return {
                'business_registration': f'{country} Business Registration Authority',
                'tax_authority': f'{country} Tax Authority', 
                'data_protection': f'{country} Data Protection Authority',
                'financial_services': f'{country} Financial Services Authority',
                'industry_regulator': f'{country} Industry Regulator'
            }

# Create global instance
regional_regulatory_agent = RegionalRegulatoryAgent() 