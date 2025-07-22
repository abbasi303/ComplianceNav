"""
Policy Matcher Agent
Cross-references retrieved regulations against startup activities using vector search
"""
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
from loguru import logger
from integrations.gemini_client import gemini_client
from core.vector_store import vector_store
import json
from datetime import datetime
from core.data_models import ComplianceGapWithSources, AnalysisQualityReport
from utils.citation_manager import citation_manager

class ComplianceGap(BaseModel):
    """Represents a compliance gap identified for the startup"""
    regulation_title: str
    regulation_content: str
    business_activity: str
    gap_type: str  # 'missing_license', 'data_protection', 'reporting', 'operational', etc.
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    recommended_actions: List[str]
    deadline: Optional[str] = None
    estimated_cost: Optional[str] = None
    country: str
    # Enhanced source attribution
    source_url: Optional[str] = None
    regulation_id: Optional[str] = None  # e.g., "GDPR Art. 32"
    authority: Optional[str] = None  # e.g., "European Commission"
    citation: Optional[str] = None  # e.g., "Regulation (EU) 2016/679, Article 32"

class MatchResult(BaseModel):
    """Result of regulation matching process"""
    compliance_gaps: List[ComplianceGap]
    compliant_areas: List[str]
    recommendations_summary: str
    overall_risk_level: str

class MatcherAgent:
    """Agent for matching regulations to startup activities and identifying compliance gaps"""
    
    def __init__(self):
        """Initialize the Matcher Agent"""
        self.agent_name = "MatcherAgent"
        logger.info(f"{self.agent_name} initialized")
    
    async def analyze_compliance_gaps(
        self, 
        startup_info: Any, 
        regulatory_documents: List[Any]
    ) -> MatchResult:
        """
        Analyze compliance gaps between startup activities and regulations
        
        Args:
            startup_info: Structured startup information
            regulatory_documents: List of regulatory documents from Scout Agent
            
        Returns:
            Detailed compliance analysis with gaps and recommendations
        """
        logger.info(f"{self.agent_name}: Analyzing compliance gaps for {startup_info.industry} startup")
        
        compliance_gaps = []
        compliant_areas = []
        
        # Analyze each business activity against relevant regulations
        for activity in startup_info.business_activities:
            activity_gaps, activity_compliant = await self._analyze_activity_compliance(
                activity, startup_info, regulatory_documents
            )
            compliance_gaps.extend(activity_gaps)
            compliant_areas.extend(activity_compliant)
        
        # Perform semantic search for additional relevant regulations
        semantic_gaps = await self._semantic_compliance_analysis(startup_info, regulatory_documents)
        compliance_gaps.extend(semantic_gaps)
        
        # Generate overall recommendations summary
        recommendations_summary = await self._generate_recommendations_summary(
            compliance_gaps, startup_info
        )
        
        # Determine overall risk level
        overall_risk_level = self._calculate_overall_risk_level(compliance_gaps)
        
        match_result = MatchResult(
            compliance_gaps=compliance_gaps,
            compliant_areas=list(set(compliant_areas)),  # Remove duplicates
            recommendations_summary=recommendations_summary,
            overall_risk_level=overall_risk_level
        )
        
        logger.info(f"{self.agent_name}: Found {len(compliance_gaps)} compliance gaps, risk level: {overall_risk_level}")
        
        # Store compliance gaps as compliance cases for historical tracking and search
        await self._store_compliance_gaps_as_cases(compliance_gaps, startup_info)
        
        return match_result
    
    async def _analyze_activity_compliance(
        self, 
        activity: str, 
        startup_info: Any, 
        regulatory_documents: List[Any]
    ) -> Tuple[List[ComplianceGap], List[str]]:
        """Analyze compliance for a specific business activity"""
        gaps = []
        compliant_areas = []
        
        # Find regulations relevant to this activity
        relevant_docs = self._filter_relevant_documents(activity, regulatory_documents)
        
        if not relevant_docs:
            # No specific regulations found - use vector search
            vector_results = vector_store.search_regulations(
                query=f"{activity} {startup_info.industry} compliance requirements",
                n_results=5,
                country_filter=startup_info.target_countries[0] if startup_info.target_countries else None
            )
            
            if vector_results:
                # Analyze vector search results
                for result in vector_results:
                    gap = await self._analyze_regulation_gap(
                        activity, result['content'], result['metadata'], startup_info
                    )
                    if gap:
                        gaps.append(gap)
        else:
            # Analyze found documents
            for doc in relevant_docs:
                gap = await self._analyze_document_gap(activity, doc, startup_info)
                if gap:
                    gaps.append(gap)
                else:
                    compliant_areas.append(f"{activity} - {doc.regulation_type}")
        
        return gaps, compliant_areas
    
    def _filter_relevant_documents(self, activity: str, documents: List[Any]) -> List[Any]:
        """Filter documents relevant to a specific business activity"""
        relevant = []
        activity_lower = activity.lower()
        
        for doc in documents:
            # Simple keyword matching - could be enhanced with ML similarity
            if any(keyword in doc.content.lower() for keyword in activity_lower.split()):
                relevant.append(doc)
            elif activity_lower in doc.title.lower():
                relevant.append(doc)
        
        return relevant
    
    async def _analyze_document_gap(
        self, 
        activity: str, 
        document: Any, 
        startup_info: Any
    ) -> Optional[ComplianceGap]:
        """Analyze a specific document for compliance gaps"""
        
        system_prompt = f"""
        You are a compliance expert analyzing whether a startup's business activity complies 
        with a specific regulation.
        
        Startup Information:
        - Industry: {startup_info.industry}
        - Business Activity: {activity}
        - Target Countries: {', '.join(startup_info.target_countries)}
        - Data Handling: {', '.join(startup_info.data_handling)}
        - Customer Types: {', '.join(startup_info.customer_types)}
        
        Regulation Information:
        - Title: {document.title}
        - Country: {document.country}
        - Content: {document.content[:1000]}...
        
        Analyze if this business activity has any compliance gaps with this regulation.
        If there are gaps, identify:
        1. The specific gap type (license, data protection, reporting, etc.)
        2. Severity (critical, high, medium, low)
        3. Description of the gap
        4. Recommended actions
        5. Any deadlines or costs
        
        If the activity is compliant, return "COMPLIANT".
        If there are gaps, provide detailed analysis.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                "Analyze this compliance scenario",
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            if "COMPLIANT" in response.upper():
                return None
            
            # Parse the response to create ComplianceGap
            gap = await self._parse_compliance_gap_response(response, activity, document)
            return gap
            
        except Exception as e:
            logger.error(f"Error analyzing document gap: {e}")
            return None
    
    async def _analyze_regulation_gap(
        self, 
        activity: str, 
        regulation_content: str, 
        metadata: Dict[str, Any], 
        startup_info: Any
    ) -> Optional[ComplianceGap]:
        """Analyze regulation from vector search results"""
        
        system_prompt = f"""
        Analyze compliance gap between startup activity and regulation.
        
        Startup Activity: {activity}
        Industry: {startup_info.industry}
        
        Regulation: {regulation_content[:800]}
        
        Identify specific compliance requirements and potential gaps.
        """
        
        try:
            response = gemini_client.generate_response_sync(
                "Analyze regulation compliance",
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Create gap from vector search result
            if len(response.strip()) > 50:  # Has substantial content
                return ComplianceGap(
                    regulation_title=metadata.get('title', 'Regulatory Requirement'),
                    regulation_content=regulation_content[:500],
                    business_activity=activity,
                    gap_type=self._infer_gap_type(response),
                    severity=self._infer_severity(response),
                    description=response[:300] + "..." if len(response) > 300 else response,
                    recommended_actions=self._extract_recommended_actions(response),
                    country=metadata.get('country', 'Unknown'),
                    deadline=None,
                    estimated_cost=None,
                    # Add source attribution from vector store metadata
                    source_url=metadata.get('url'),
                    regulation_id=metadata.get('regulation_id'),
                    authority=metadata.get('authority'),
                    citation=metadata.get('citation_format')
                )
            
        except Exception as e:
            logger.error(f"Error analyzing regulation gap: {e}")
        
        return None
    
    async def _semantic_compliance_analysis(
        self, 
        startup_info: Any, 
        regulatory_documents: List[Any]
    ) -> List[ComplianceGap]:
        """Perform semantic analysis to find additional compliance gaps"""
        gaps = []
        
        # Search for industry-specific regulations
        industry_query = f"{startup_info.industry} regulatory compliance requirements"
        industry_results = vector_store.search_regulations(
            query=industry_query,
            n_results=3,
            country_filter=startup_info.target_countries[0] if startup_info.target_countries else None
        )
        
        # Search for data protection regulations if applicable
        if startup_info.data_handling:
            data_query = f"data protection privacy {' '.join(startup_info.data_handling)} regulations"
            data_results = vector_store.search_regulations(
                query=data_query,
                n_results=3
            )
            industry_results.extend(data_results)
        
        # Analyze semantic search results
        for result in industry_results:
            gap = await self._create_semantic_gap(result, startup_info)
            if gap:
                gaps.append(gap)
        
        return gaps
    
    async def _create_semantic_gap(self, search_result: Dict[str, Any], startup_info: Any) -> Optional[ComplianceGap]:
        """Create a compliance gap from semantic search result"""
        try:
            content = search_result['content']
            metadata = search_result['metadata']
            
            # Use Gemini to analyze the semantic match
            system_prompt = f"""
            Quick compliance analysis:
            Startup: {startup_info.industry} in {', '.join(startup_info.target_countries)}
            Regulation: {content[:400]}
            
            Identify any major compliance requirement that might apply to this startup.
            Be concise.
            """
            
            analysis = gemini_client.generate_response_sync(
                "Analyze semantic compliance match",
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            if len(analysis.strip()) > 30:  # Has meaningful content
                return ComplianceGap(
                    regulation_title=metadata.get('title', 'Regulatory Requirement'),
                    regulation_content=content[:400],
                    business_activity="General Operations",
                    gap_type="regulatory",
                    severity="medium",
                    description=analysis[:250],
                    recommended_actions=["Review full regulation", "Consult legal expert"],
                    country=metadata.get('country', 'Unknown'),
                    # Add source attribution from semantic search metadata
                    source_url=metadata.get('url'),
                    regulation_id=metadata.get('regulation_id'),
                    authority=metadata.get('authority'),
                    citation=metadata.get('citation_format')
                )
        
        except Exception as e:
            logger.error(f"Error creating semantic gap: {e}")
        
        return None
    
    async def _parse_compliance_gap_response(
        self, 
        response: str, 
        activity: str, 
        document: Any
    ) -> ComplianceGap:
        """Parse Gemini response into structured ComplianceGap with proper source attribution"""
        
        # Extract recommended actions (simple parsing)
        actions = self._extract_recommended_actions(response)
        
        return ComplianceGap(
            regulation_title=document.title,
            regulation_content=document.content[:400],
            business_activity=activity,
            gap_type=self._infer_gap_type(response),
            severity=self._infer_severity(response),
            description=response[:300] + "..." if len(response) > 300 else response,
            recommended_actions=actions,
            country=document.country,
            deadline=self._extract_deadline(response),
            estimated_cost=self._extract_cost(response),
            # Add source attribution fields
            source_url=getattr(document, 'url', None),
            regulation_id=getattr(document, 'regulation_id', None),
            authority=getattr(document, 'authority', None),
            citation=getattr(document, 'citation_format', None)
        )
    
    def _infer_gap_type(self, response: str) -> str:
        """Infer gap type from response content"""
        response_lower = response.lower()
        
        if any(term in response_lower for term in ['license', 'permit', 'authorization']):
            return 'licensing'
        elif any(term in response_lower for term in ['data', 'privacy', 'gdpr', 'personal']):
            return 'data_protection'
        elif any(term in response_lower for term in ['report', 'filing', 'disclosure']):
            return 'reporting'
        elif any(term in response_lower for term in ['tax', 'vat', 'corporate']):
            return 'tax_compliance'
        else:
            return 'operational'
    
    def _infer_severity(self, response: str) -> str:
        """Infer severity from response content"""
        response_lower = response.lower()
        
        if any(term in response_lower for term in ['critical', 'mandatory', 'required', 'must']):
            return 'critical'
        elif any(term in response_lower for term in ['important', 'significant', 'penalty']):
            return 'high'
        elif any(term in response_lower for term in ['should', 'recommended', 'advisable']):
            return 'medium'
        else:
            return 'low'
    
    def _extract_recommended_actions(self, response: str) -> List[str]:
        """Extract recommended actions from response"""
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or 'recommend' in line.lower():
                action = line.lstrip('- •').strip()
                if len(action) > 10:
                    actions.append(action)
        
        # Fallback if no actions found
        if not actions:
            actions = ["Consult with legal expert", "Review full regulation details"]
        
        return actions[:5]  # Limit to 5 actions
    
    def _extract_deadline(self, response: str) -> Optional[str]:
        """Extract deadline information from response"""
        import re
        deadline_patterns = [
            r'deadline.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'by (\w+ \d{1,2}, \d{4})',
            r'within (\d+ \w+)',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_cost(self, response: str) -> Optional[str]:
        """Extract cost information from response"""
        import re
        cost_patterns = [
            r'[\$€£][\d,]+',
            r'\d+\s*(?:euro|dollars|EUR|USD)',
            r'fee.*?(\d+)',
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    async def _generate_recommendations_summary(
        self, 
        compliance_gaps: List[ComplianceGap], 
        startup_info: Any
    ) -> str:
        """Generate overall recommendations summary"""
        
        if not compliance_gaps:
            return "Your startup appears to be compliant with the major regulatory requirements. Continue monitoring for updates."
        
        system_prompt = f"""
        Create a concise executive summary of compliance recommendations for a {startup_info.industry} 
        startup targeting {', '.join(startup_info.target_countries)}.
        
        Key compliance gaps found:
        {len(compliance_gaps)} total gaps
        Critical: {len([g for g in compliance_gaps if g.severity == 'critical'])}
        High: {len([g for g in compliance_gaps if g.severity == 'high'])}
        
        Provide actionable, prioritized recommendations in 2-3 paragraphs.
        """
        
        gap_summary = "\n".join([
            f"- {gap.gap_type}: {gap.description[:100]}..." 
            for gap in compliance_gaps[:5]
        ])
        
        try:
            summary = gemini_client.generate_response_sync(
                f"Gap Details:\n{gap_summary}\n\nCreate executive summary of recommendations.",
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating recommendations summary: {e}")
            return f"Found {len(compliance_gaps)} compliance gaps requiring attention. Prioritize critical and high-severity items first."
    
    def _calculate_overall_risk_level(self, compliance_gaps: List[ComplianceGap]) -> str:
        """Calculate overall compliance risk level"""
        if not compliance_gaps:
            return "low"
        
        critical_count = len([g for g in compliance_gaps if g.severity == 'critical'])
        high_count = len([g for g in compliance_gaps if g.severity == 'high'])
        
        if critical_count >= 2:
            return "critical"
        elif critical_count >= 1 or high_count >= 3:
            return "high"
        elif high_count >= 1 or len(compliance_gaps) >= 5:
            return "medium"
        else:
            return "low"
    
    async def _store_compliance_gaps_as_cases(self, compliance_gaps: List[ComplianceGap], startup_info: Any):
        """Store identified compliance gaps as compliance cases for historical tracking"""
        try:
            for gap in compliance_gaps:
                case_description = f"""
                Compliance Gap Identified: {gap.regulation_title}
                
                Business Activity: {gap.business_activity}
                Gap Type: {gap.gap_type.replace('_', ' ').title()}
                Severity: {gap.severity.upper()}
                
                Description: {gap.description}
                
                Recommended Actions:
                {chr(10).join([f"• {action}" for action in gap.recommended_actions])}
                """
                
                outcome = f"Gap identified - {gap.severity} priority action required"
                
                metadata = {
                    'industry': startup_info.industry,
                    'country': gap.country,
                    'gap_type': gap.gap_type,
                    'severity': gap.severity,
                    'business_activity': gap.business_activity,
                    'regulation_title': gap.regulation_title,
                    'case_type': 'compliance_gap',
                    'analysis_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Add optional fields if available
                if gap.deadline:
                    metadata['deadline'] = gap.deadline
                if gap.estimated_cost:
                    metadata['estimated_cost'] = gap.estimated_cost
                if gap.authority:
                    metadata['authority'] = gap.authority
                
                case_id = vector_store.add_compliance_case(
                    case_description=case_description.strip(),
                    outcome=outcome,
                    metadata=metadata
                )
                
                logger.debug(f"Stored compliance gap as case: {case_id}")
                
        except Exception as e:
            logger.error(f"Error storing compliance gaps as cases: {e}")
            # Don't fail the analysis if case storage fails

    async def create_sourced_compliance_gap(self, gap_data: dict, related_documents: List[Any]) -> ComplianceGapWithSources:
        """Create a compliance gap with proper source tracking"""
        try:
            # Create basic gap
            sourced_gap = ComplianceGapWithSources(
                title=gap_data.get('title', 'Unknown Gap'),
                gap_type=gap_data.get('gap_type', 'unknown'),
                severity=gap_data.get('severity', 'medium'),
                description=gap_data.get('description', ''),
                recommended_actions=gap_data.get('recommended_actions', []),
                country=gap_data.get('country', ''),
                deadline=gap_data.get('deadline'),
                estimated_cost=gap_data.get('estimated_cost')
            )
            
            # Track sources from related documents
            primary_sources = []
            supporting_sources = []
            
            for doc in related_documents:
                try:
                    # Create source from document
                    doc_data = {
                        'title': getattr(doc, 'title', 'Unknown Document'),
                        'content': getattr(doc, 'content', ''),
                        'url': getattr(doc, 'url', None),
                        'authority': getattr(doc, 'authority', None),
                        'source': getattr(doc, 'source', ''),
                        'last_updated': getattr(doc, 'last_updated', None)
                    }
                    
                    source = citation_manager.create_source_from_document(doc_data)
                    citation = citation_manager.generate_citation(source, gap_data.get('description', '')[:200])
                    
                    # Categorize based on source quality
                    if source.source_quality.value in ['primary', 'secondary']:
                        primary_sources.append(citation)
                    else:
                        supporting_sources.append(citation)
                        
                except Exception as e:
                    logger.warning(f"Could not create source for document: {e}")
                    continue
            
            sourced_gap.primary_sources = primary_sources
            sourced_gap.supporting_sources = supporting_sources
            sourced_gap.source_coverage = min(1.0, len(primary_sources + supporting_sources) / max(1, len(gap_data.get('recommended_actions', []))))
            sourced_gap.ai_confidence = 0.7 if primary_sources else 0.4  # Lower confidence without primary sources
            
            # Identify missing source areas
            if not primary_sources:
                sourced_gap.missing_sources.append("No official regulatory sources found")
            if sourced_gap.source_coverage < 0.5:
                sourced_gap.missing_sources.append("Insufficient source coverage for all requirements")
                
            return sourced_gap
            
        except Exception as e:
            logger.error(f"Error creating sourced compliance gap: {e}")
            # Return basic gap as fallback
            return ComplianceGapWithSources(
                title=gap_data.get('title', 'Unknown Gap'),
                gap_type=gap_data.get('gap_type', 'unknown'),
                severity=gap_data.get('severity', 'medium'),
                description=gap_data.get('description', ''),
                recommended_actions=gap_data.get('recommended_actions', []),
                country=gap_data.get('country', ''),
                deadline=gap_data.get('deadline'),
                estimated_cost=gap_data.get('estimated_cost'),
                missing_sources=["Error tracking sources - manual verification required"],
                ai_confidence=0.3
            )

# Global matcher agent instance
matcher_agent = MatcherAgent() 