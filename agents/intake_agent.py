"""
Autonomous Intake Agent
Parses user descriptions of startups and extracts key information for compliance analysis
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
from integrations.gemini_client import gemini_client

class StartupInfo(BaseModel):
    """Structured startup information"""
    company_name: Optional[str] = None
    industry: str
    business_activities: List[str]
    target_countries: List[str]
    business_model: Optional[str] = None
    data_handling: List[str] = []
    customer_types: List[str] = []
    revenue_model: Optional[str] = None
    stage: Optional[str] = None
    compliance_concerns: List[str] = []

class IntakeAgent:
    """Autonomous agent for parsing and structuring startup information"""
    
    def __init__(self):
        """Initialize the Intake Agent"""
        self.agent_name = "IntakeAgent"
        logger.info(f"{self.agent_name} initialized")
    
    def parse_startup_description(self, user_input: str) -> StartupInfo:
        """
        Parse user description and extract structured startup information with self-validation
        
        Args:
            user_input: Raw user description of their startup
            
        Returns:
            Structured StartupInfo object
        """
        logger.info(f"{self.agent_name}: Processing startup description with self-validation")
        
        # Step 1: Initial extraction
        initial_extraction = self._extract_startup_info(user_input)
        
        # Step 2: Self-validation
        validation_result = self._validate_extraction(user_input, initial_extraction)
        
        # Step 3: Re-extract if confidence is low
        if validation_result['confidence'] < 0.7:
            logger.info(f"{self.agent_name}: Low confidence ({validation_result['confidence']:.2f}), re-extracting with focused approach")
            enhanced_extraction = self._focused_re_extraction(user_input, validation_result)
            
            # Validate the re-extraction
            revalidation = self._validate_extraction(user_input, enhanced_extraction)
            if revalidation['confidence'] > validation_result['confidence']:
                logger.info(f"{self.agent_name}: Improved confidence from {validation_result['confidence']:.2f} to {revalidation['confidence']:.2f}")
                final_extraction = enhanced_extraction
            else:
                logger.warning(f"{self.agent_name}: Re-extraction didn't improve, using best available")
                final_extraction = initial_extraction if validation_result['confidence'] > revalidation['confidence'] else enhanced_extraction
        else:
            logger.info(f"{self.agent_name}: High confidence ({validation_result['confidence']:.2f}), using initial extraction")
            final_extraction = initial_extraction
        
        logger.info(f"{self.agent_name}: Final result - Industry: {final_extraction.industry}, Countries: {final_extraction.target_countries}")
        return final_extraction

    def _extract_startup_info(self, user_input: str) -> StartupInfo:
        """Original extraction logic"""
        system_prompt = """
        You are an expert business analyst specializing in regulatory compliance. 
        Analyze the user's startup description and extract key information needed for compliance analysis.
        
        Focus on identifying:
        1. Industry/sector (healthcare, fintech, e-commerce, etc.)
        2. Specific business activities
        3. Target countries/markets
        4. Data handling practices (personal data, financial data, health data)
        5. Customer types (B2B, B2C, businesses, individuals)
        6. Revenue model if mentioned
        7. Any compliance concerns mentioned
        
        Be specific and comprehensive in your analysis.
        """
        
        extraction_schema = {
            "company_name": "string or null",
            "industry": "string (required)",
            "business_activities": "array of strings",
            "target_countries": "array of strings", 
            "business_model": "string or null",
            "data_handling": "array of strings",
            "customer_types": "array of strings",
            "revenue_model": "string or null",
            "stage": "string or null (startup, MVP, scaling, established)",
            "compliance_concerns": "array of strings"
        }
        
        try:
            # Extract structured data using Gemini
            extracted_data = gemini_client.extract_structured_data(
                f"{system_prompt}\n\nStartup Description: {user_input}",
                extraction_schema
            )
            
            # Validate and clean the extracted data
            if not extracted_data or not isinstance(extracted_data, dict):
                logger.warning(f"{self.agent_name}: Empty or invalid data from Gemini, using fallback parsing")
                extracted_data = self._fallback_parsing(user_input)
            
            # Ensure required fields are present
            if not extracted_data.get('industry'):
                extracted_data['industry'] = self._extract_industry_fallback(user_input)
            if not extracted_data.get('business_activities'):
                extracted_data['business_activities'] = self._extract_activities_fallback(user_input)
            if not extracted_data.get('target_countries'):
                extracted_data['target_countries'] = self._extract_countries_fallback(user_input)
            
            # Convert to StartupInfo object
            startup_info = StartupInfo(**extracted_data)
            return startup_info
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error in initial extraction: {e}")
            # Return robust fallback info
            fallback_data = self._fallback_parsing(user_input)
            return StartupInfo(**fallback_data)

    def _validate_extraction(self, original_input: str, extracted_info: StartupInfo) -> Dict[str, Any]:
        """Validate extraction quality against original input"""
        
        validation_prompt = f"""
        Validate this information extraction for accuracy:
        
        ORIGINAL USER INPUT: "{original_input}"
        
        EXTRACTED INFORMATION:
        - Industry: {extracted_info.industry}
        - Countries: {', '.join(extracted_info.target_countries)}
        - Business Activities: {', '.join(extracted_info.business_activities)}
        - Data Handling: {', '.join(extracted_info.data_handling or [])}
        
        VALIDATION CHECKLIST:
        1. Industry Accuracy: Did we correctly identify specific industry terms? 
           - Look for: robotics, fintech, healthcare, e-commerce, AI, blockchain, etc.
           - "Technology" is too generic if user mentioned specific industry
        
        2. Geographic Accuracy: Did we correctly identify all countries mentioned?
           - Look for: Pakistan, India, Germany, USA, UK, etc.
           - "Global" is too generic if user mentioned specific countries
        
        3. Business Context: Did we capture the specific business activities?
           - Manufacturing, consulting, software development, etc.
        
        4. Completeness: Did we miss any important details from the original input?
        
        SCORING:
        - 1.0 = Perfect extraction, all key details captured accurately
        - 0.8 = Good extraction, minor details missed  
        - 0.6 = Acceptable extraction, some important details missed
        - 0.4 = Poor extraction, major details missed or incorrect
        - 0.2 = Very poor extraction, mostly incorrect
        
        Return ONLY a JSON object:
        {{
            "confidence": 0.0-1.0,
            "issues": ["list", "of", "specific", "problems"],
            "missing_terms": ["terms", "that", "were", "missed"],
            "suggestions": ["specific", "improvements", "needed"]
        }}
        """
        
        try:
            validation_response = gemini_client.generate_response_sync(
                validation_prompt,
                temperature=0.1,
                system_prompt="You are a quality assurance specialist for information extraction. Be thorough and critical."
            )
            
            # Parse validation result
            import json
            clean_response = validation_response.strip().strip('```json').strip('```').strip()
            validation_result = json.loads(clean_response)
            
            return {
                'confidence': float(validation_result.get('confidence', 0.5)),
                'issues': validation_result.get('issues', []),
                'missing_terms': validation_result.get('missing_terms', []),
                'suggestions': validation_result.get('suggestions', [])
            }
            
        except Exception as e:
            logger.error(f"Error in validation: {e}")
            return {
                'confidence': 0.6,  # Neutral confidence if validation fails
                'issues': ['Validation system error'],
                'missing_terms': [],
                'suggestions': ['Manual review recommended']
            }

    def _focused_re_extraction(self, original_input: str, validation_issues: Dict[str, Any]) -> StartupInfo:
        """Re-extract with focused prompts based on validation issues"""
        
        focused_prompt = f"""
        FOCUSED RE-EXTRACTION: The initial analysis missed important details.
        
        ORIGINAL USER INPUT: "{original_input}"
        
        IDENTIFIED ISSUES: {', '.join(validation_issues.get('issues', []))}
        MISSING TERMS: {', '.join(validation_issues.get('missing_terms', []))}
        
        SPECIAL FOCUS AREAS:
        - Look for SPECIFIC industry terms (not generic "technology")
        - Look for SPECIFIC country names (not generic "global") 
        - Look for SPECIFIC business activities (manufacturing, consulting, etc.)
        - Pay attention to technical terms that indicate industry specialization
        
        INDUSTRY DETECTION:
        - "robotics", "robotic", "robot" → Robotics/Hardware
        - "fintech", "financial", "payment" → Financial Technology  
        - "healthcare", "medical", "telemedicine" → Healthcare
        - "AI", "machine learning", "artificial intelligence" → AI/ML
        - "blockchain", "crypto" → Blockchain/Crypto
        
        COUNTRY DETECTION:
        - Look for ANY country names mentioned
        - Regional indicators: "South Asian", "European", "Asian markets"
        - Don't default to "Global" unless explicitly stated
        
        Extract with MAXIMUM SPECIFICITY:
        """
        
        extraction_schema = {
            "company_name": "string or null",
            "industry": "string (SPECIFIC industry, avoid generic terms)",
            "business_activities": "array of SPECIFIC activities",
            "target_countries": "array of SPECIFIC countries mentioned", 
            "business_model": "string or null",
            "data_handling": "array of strings",
            "customer_types": "array of strings",
            "revenue_model": "string or null",
            "stage": "string or null",
            "compliance_concerns": "array of strings"
        }
        
        try:
            enhanced_data = gemini_client.extract_structured_data(
                focused_prompt,
                extraction_schema
            )
            
            if not enhanced_data or not isinstance(enhanced_data, dict):
                logger.warning("Re-extraction failed, using enhanced fallback")
                enhanced_data = self._fallback_parsing(original_input)
            
            # Ensure critical fields
            if not enhanced_data.get('industry') or enhanced_data['industry'].lower() in ['technology', 'tech', 'general']:
                enhanced_data['industry'] = self._extract_specific_industry(original_input)
            
            if not enhanced_data.get('target_countries') or 'global' in [c.lower() for c in enhanced_data.get('target_countries', [])]:
                enhanced_data['target_countries'] = self._extract_specific_countries(original_input)
                
            return StartupInfo(**enhanced_data)
            
        except Exception as e:
            logger.error(f"Error in focused re-extraction: {e}")
            fallback_data = self._fallback_parsing(original_input)
            return StartupInfo(**fallback_data)

    def _extract_specific_industry(self, text: str) -> str:
        """Extract specific industry with keyword matching"""
        text_lower = text.lower()
        
        industry_keywords = {
            'robotics': ['robot', 'robotic', 'robotics', 'automation', 'manufacturing', 'hardware'],
            'fintech': ['fintech', 'financial', 'payment', 'banking', 'finance', 'lending'],
            'healthcare': ['health', 'medical', 'telemedicine', 'patient', 'doctor', 'clinical'],
            'e-commerce': ['ecommerce', 'e-commerce', 'online store', 'marketplace', 'retail'],
            'ai/ml': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning'],
            'blockchain': ['blockchain', 'crypto', 'cryptocurrency', 'bitcoin', 'defi'],
            'saas': ['saas', 'software as a service', 'cloud', 'platform'],
            'edtech': ['education', 'learning', 'edtech', 'training', 'course']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry.title().replace('/', ' & ')
        
        return "Technology"  # Fallback

    def _extract_specific_countries(self, text: str) -> List[str]:
        """Extract specific countries mentioned"""
        text_lower = text.lower()
        
        countries = [
            'pakistan', 'india', 'bangladesh', 'germany', 'france', 'uk', 'united kingdom',
            'usa', 'united states', 'canada', 'australia', 'singapore', 'malaysia',
            'indonesia', 'thailand', 'vietnam', 'philippines', 'china', 'japan',
            'south korea', 'brazil', 'mexico', 'argentina', 'chile', 'netherlands',
            'sweden', 'norway', 'denmark', 'finland', 'switzerland', 'austria',
            'italy', 'spain', 'portugal', 'poland', 'czech republic', 'hungary',
            'turkey', 'israel', 'uae', 'saudi arabia', 'egypt', 'south africa'
        ]
        
        found_countries = []
        for country in countries:
            if country in text_lower:
                # Normalize country names
                country_map = {
                    'usa': 'United States',
                    'uk': 'United Kingdom', 
                    'uae': 'United Arab Emirates',
                    'saudi arabia': 'Saudi Arabia',
                    'south africa': 'South Africa',
                    'south korea': 'South Korea',
                    'united states': 'United States',
                    'united kingdom': 'United Kingdom'
                }
                normalized = country_map.get(country, country.title())
                if normalized not in found_countries:
                    found_countries.append(normalized)
        
        # Check for regional indicators
        if 'south asia' in text_lower or 'south asian' in text_lower:
            if 'Pakistan' not in found_countries:
                found_countries.append('Pakistan')
        
        return found_countries if found_countries else ['Global']

    def _enhanced_fallback_parsing(self, text: str, validation_issues: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback parsing that uses validation insights"""
        
        return {
            "company_name": None,
            "industry": self._extract_specific_industry(text),
            "business_activities": self._extract_activities_fallback(text),
            "target_countries": self._extract_specific_countries(text),
            "business_model": None,
            "data_handling": self._extract_data_handling_fallback(text),
            "customer_types": ["general users"],
            "revenue_model": None,
            "stage": "startup",
            "compliance_concerns": []
        }
    
    def generate_research_queries(self, startup_info: StartupInfo) -> List[Dict[str, str]]:
        """
        Generate targeted research queries based on startup information
        
        Args:
            startup_info: Structured startup information
            
        Returns:
            List of research queries for the Scout Agent
        """
        logger.info(f"{self.agent_name}: Generating research queries")
        
        system_prompt = """
        You are a regulatory research specialist. Based on the startup information provided,
        generate specific, targeted research queries that will help find relevant regulations
        and compliance requirements.
        
        Create queries that are:
        1. Specific to the industry and business activities
        2. Country/region-specific
        3. Data protection focused (if applicable)
        4. License and permit focused
        5. Industry-specific compliance focused
        
        Return 5-10 focused research queries that will yield actionable regulatory information.
        """
        
        startup_summary = f"""
        Industry: {startup_info.industry}
        Business Activities: {', '.join(startup_info.business_activities)}
        Target Countries: {', '.join(startup_info.target_countries)}
        Data Handling: {', '.join(startup_info.data_handling)}
        Customer Types: {', '.join(startup_info.customer_types)}
        """
        
        try:
            response = gemini_client.generate_response_sync(
                f"Startup Information:\n{startup_summary}\n\nGenerate specific regulatory research queries for this startup.",
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Parse the response into structured queries
            queries = self._parse_research_queries(response, startup_info)
            
            logger.info(f"{self.agent_name}: Generated {len(queries)} research queries")
            return queries
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error generating research queries: {e}")
            # Return fallback queries
            return self._generate_fallback_queries(startup_info)
    
    def _parse_research_queries(self, response: str, startup_info: StartupInfo) -> List[Dict[str, str]]:
        """Parse Gemini response into structured research queries"""
        queries = []
        
        # Split response into lines and extract queries
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('1') or 'regulation' in line.lower()):
                query_text = line.lstrip('- •123456789.').strip()
                if len(query_text) > 10:  # Valid query
                    # Determine query type based on content
                    query_type = self._categorize_query(query_text)
                    queries.append({
                        'query': query_text,
                        'type': query_type,
                        'priority': 'high' if any(country in query_text.lower() for country in [c.lower() for c in startup_info.target_countries]) else 'medium'
                    })
        
        return queries[:10]  # Limit to 10 queries
    
    def _categorize_query(self, query: str) -> str:
        """Categorize a research query by type"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['license', 'permit', 'authorization', 'registration']):
            return 'licensing'
        elif any(term in query_lower for term in ['data', 'privacy', 'gdpr', 'protection']):
            return 'data_protection'
        elif any(term in query_lower for term in ['tax', 'vat', 'corporate', 'business registration']):
            return 'business_setup'
        elif any(term in query_lower for term in ['industry', 'sector', 'specific']):
            return 'industry_specific'
        else:
            return 'general'
    
    def _generate_fallback_queries(self, startup_info: StartupInfo) -> List[Dict[str, str]]:
        """Generate fallback queries when AI generation fails"""
        queries = []
        
        for country in startup_info.target_countries:
            queries.extend([
                {
                    'query': f"{startup_info.industry} business regulations in {country}",
                    'type': 'industry_specific',
                    'priority': 'high'
                },
                {
                    'query': f"Business registration requirements {country}",
                    'type': 'business_setup', 
                    'priority': 'medium'
                },
                {
                    'query': f"Data protection laws {country}",
                    'type': 'data_protection',
                    'priority': 'high' if startup_info.data_handling else 'low'
                }
            ])
        
        return queries[:8]  # Limit to avoid overwhelming

    def _extract_industry_fallback(self, text: str) -> str:
        """Enhanced industry extraction fallback"""
        return self._extract_specific_industry(text)
        
    def _extract_activities_fallback(self, text: str) -> List[str]:
        """Enhanced business activities extraction"""
        text_lower = text.lower()
        activities = []
        
        activity_patterns = {
            'software development': ['software', 'development', 'coding', 'programming'],
            'manufacturing': ['manufacturing', 'production', 'assembly', 'factory'],
            'consulting': ['consulting', 'advisory', 'guidance', 'consultation'],
            'e-commerce': ['online store', 'marketplace', 'selling online', 'retail'],
            'data processing': ['data processing', 'analytics', 'data analysis'],
            'payment processing': ['payment', 'transactions', 'financial services'],
            'telemedicine': ['telemedicine', 'remote healthcare', 'virtual consultation'],
            'robotics manufacturing': ['robot', 'robotic', 'automation', 'hardware'],
            'platform operations': ['platform', 'service', 'hosting', 'cloud'],
            'content creation': ['content', 'media', 'publishing', 'blogging']
        }
        
        for activity, keywords in activity_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                if activity not in activities:
                    activities.append(activity)
        
        # If no specific activities found, infer from industry context
        if not activities:
            if any(term in text_lower for term in ['robot', 'robotic', 'manufacturing']):
                activities.append('robotics manufacturing')
            elif any(term in text_lower for term in ['software', 'platform', 'app']):
                activities.append('software development')
            else:
                activities.append('general business operations')
        
        return activities

    def _extract_countries_fallback(self, text: str) -> List[str]:
        """Enhanced countries extraction fallback"""
        return self._extract_specific_countries(text)

    def _extract_data_handling_fallback(self, text: str) -> List[str]:
        """Extract data handling practices"""
        text_lower = text.lower()
        data_types = []
        
        data_patterns = {
            'personal data': ['personal', 'user data', 'customer data', 'individual'],
            'financial data': ['financial', 'payment', 'transaction', 'banking', 'money'],
            'health data': ['health', 'medical', 'patient', 'clinical', 'healthcare'],
            'biometric data': ['biometric', 'fingerprint', 'facial recognition', 'iris'],
            'location data': ['location', 'gps', 'geolocation', 'tracking'],
            'behavioral data': ['behavior', 'usage', 'analytics', 'tracking'],
            'sensitive data': ['sensitive', 'confidential', 'private', 'secure']
        }
        
        for data_type, keywords in data_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                if data_type not in data_types:
                    data_types.append(data_type)
        
        # Industry-specific defaults
        if not data_types:
            if any(term in text_lower for term in ['fintech', 'financial', 'payment']):
                data_types.extend(['personal data', 'financial data'])
            elif any(term in text_lower for term in ['health', 'medical', 'telemedicine']):
                data_types.extend(['personal data', 'health data'])
            elif any(term in text_lower for term in ['robot', 'iot', 'sensor']):
                data_types.extend(['usage data', 'technical data'])
        
        return data_types

    def _fallback_parsing(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback parsing with better intelligence"""
        return {
            "company_name": None,
            "industry": self._extract_specific_industry(text),
            "business_activities": self._extract_activities_fallback(text),
            "target_countries": self._extract_specific_countries(text),
            "business_model": self._infer_business_model(text),
            "data_handling": self._extract_data_handling_fallback(text),
            "customer_types": self._infer_customer_types(text),
            "revenue_model": None,
            "stage": self._infer_stage(text),
            "compliance_concerns": []
        }

    def _infer_business_model(self, text: str) -> str:
        """Infer business model from text"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['saas', 'subscription', 'monthly', 'recurring']):
            return 'SaaS'
        elif any(term in text_lower for term in ['marketplace', 'commission', 'platform']):
            return 'Marketplace'
        elif any(term in text_lower for term in ['manufacturing', 'hardware', 'product']):
            return 'Product Sales'
        elif any(term in text_lower for term in ['consulting', 'service', 'advisory']):
            return 'Services'
        
        return None

    def _infer_customer_types(self, text: str) -> List[str]:
        """Infer customer types from text"""
        text_lower = text.lower()
        customer_types = []
        
        if any(term in text_lower for term in ['b2b', 'business', 'enterprise', 'company']):
            customer_types.append('businesses')
        if any(term in text_lower for term in ['b2c', 'consumer', 'individual', 'user', 'people']):
            customer_types.append('individuals')
        if any(term in text_lower for term in ['government', 'public sector', 'municipality']):
            customer_types.append('government')
        
        return customer_types if customer_types else ['general users']

    def _infer_stage(self, text: str) -> str:
        """Infer startup stage from text"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['launching', 'starting', 'new', 'beginning']):
            return 'startup'
        elif any(term in text_lower for term in ['mvp', 'prototype', 'beta']):
            return 'mvp'
        elif any(term in text_lower for term in ['scaling', 'growth', 'expanding']):
            return 'scaling'
        elif any(term in text_lower for term in ['established', 'mature', 'years']):
            return 'established'
        
        return 'startup'

# Global intake agent instance
intake_agent = IntakeAgent() 