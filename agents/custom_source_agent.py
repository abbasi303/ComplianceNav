"""
Custom Source Agent
Processes user-provided regulation links, documents, and custom sources
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup
from integrations.gemini_client import gemini_client
import PyPDF2
import docx
import io
import re

class CustomSource(BaseModel):
    """User-provided custom source"""
    type: str  # 'url', 'text', 'file'
    content: Optional[str] = None  # Raw text or file content
    url: Optional[str] = None  # URL for URL-type sources
    title: Optional[str] = None  # Source title (for security validation)
    description: Optional[str] = None  # Source description (for security validation)
    user_description: Optional[str] = None  # User's description of what this source is (backward compatibility)
    source_name: Optional[str] = None  # User-provided name (backward compatibility)
    relevance_note: Optional[str] = None  # Why user thinks this is relevant
    priority: str = "high"  # User sources get high priority by default

class ProcessedCustomSource(BaseModel):
    """Processed custom source ready for analysis"""
    original_source: CustomSource
    extracted_content: str
    document_type: str  # 'regulation', 'guidance', 'proposal', 'legal_document'
    authority: Optional[str] = None
    regulation_ids: List[str] = []  # Extracted regulation references
    key_requirements: List[str] = []  # AI-extracted key compliance points
    confidence_score: float = 0.8  # Default high confidence for user sources

class CustomSourceAgent:
    """Agent for processing user-provided custom sources"""
    
    def __init__(self):
        self.agent_name = "CustomSourceAgent"
        logger.info(f"{self.agent_name} initialized")
    
    async def process_custom_sources(
        self, 
        custom_sources: List[CustomSource], 
        startup_info: Any
    ) -> List[ProcessedCustomSource]:
        """Process all user-provided custom sources"""
        
        logger.info(f"{self.agent_name}: Processing {len(custom_sources)} custom sources")
        
        processed_sources = []
        
        for source in custom_sources:
            try:
                processed = await self._process_single_source(source, startup_info)
                if processed:
                    processed_sources.append(processed)
                    
            except Exception as e:
                logger.error(f"Error processing custom source: {e}")
                continue
        
        logger.info(f"{self.agent_name}: Successfully processed {len(processed_sources)} custom sources")
        return processed_sources
    
    async def _process_single_source(
        self, 
        source: CustomSource, 
        startup_info: Any
    ) -> Optional[ProcessedCustomSource]:
        """Process a single custom source"""
        
        logger.info(f"{self.agent_name}: Processing {source.type} source")
        
        # Extract content based on source type
        extracted_content = await self._extract_content(source)
        if not extracted_content:
            logger.warning(f"Could not extract content from {source.type} source")
            return None
        
        # Analyze the extracted content with AI
        analysis = await self._analyze_custom_content(extracted_content, source, startup_info)
        
        # Create processed source
        processed = ProcessedCustomSource(
            original_source=source,
            extracted_content=extracted_content,
            document_type=analysis.get('document_type', 'unknown'),
            authority=analysis.get('authority'),
            regulation_ids=analysis.get('regulation_ids', []),
            key_requirements=analysis.get('key_requirements', []),
            confidence_score=analysis.get('confidence_score', 0.8)
        )
        
        return processed
    
    async def _extract_content(self, source: CustomSource) -> Optional[str]:
        """Extract content from different source types"""
        
        if source.type == 'url':
            url_content = getattr(source, 'url', None) or source.content  # Support both 'url' and 'content' fields
            return await self._extract_from_url(url_content)
        
        elif source.type == 'text':
            return source.content
        
        elif source.type == 'file':
            # Handle file content based on extension or content type
            if isinstance(source.content, bytes):
                # File upload - detect type and extract
                return await self._extract_from_file_bytes(source.content, source.source_name)
            else:
                return str(source.content)
        
        else:
            logger.warning(f"Unknown source type: {source.type}")
            return None
    
    async def _extract_from_file_bytes(self, file_bytes: bytes, filename: Optional[str] = None) -> Optional[str]:
        """Extract text from file bytes"""
        try:
            if filename:
                if filename.lower().endswith('.pdf'):
                    return await self._extract_from_pdf_bytes(file_bytes)
                elif filename.lower().endswith(('.docx', '.doc')):
                    return await self._extract_from_doc_bytes(file_bytes)
                elif filename.lower().endswith('.txt'):
                    return file_bytes.decode('utf-8')
            
            # Try to detect content type and extract accordingly
            try:
                # Try UTF-8 text first
                return file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # If not text, try PDF extraction
                return await self._extract_from_pdf_bytes(file_bytes)
                
        except Exception as e:
            logger.error(f"Error extracting from file bytes: {e}")
            return None
    
    async def _extract_from_pdf_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return None
    
    async def _extract_from_doc_bytes(self, doc_bytes: bytes) -> Optional[str]:
        """Extract text from Word document bytes"""
        try:
            doc_file = io.BytesIO(doc_bytes)
            doc = docx.Document(doc_file)
            
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting Word doc: {e}")
            return None
    
    async def _extract_from_url(self, url: str) -> Optional[str]:
        """Extract content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        if 'text/html' in response.headers.get('content-type', ''):
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Remove script and style elements
                            for script in soup(["script", "style"]):
                                script.extract()
                            
                            # Get text content
                            text = soup.get_text()
                            
                            # Clean up whitespace
                            lines = (line.strip() for line in text.splitlines())
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            text = '\n'.join(chunk for chunk in chunks if chunk)
                            
                            return text[:50000]  # Limit to 50KB for processing
                        
                        elif 'application/pdf' in response.headers.get('content-type', ''):
                            # Handle PDF URLs
                            pdf_content = await response.read()
                            return await self._extract_pdf_content(pdf_content)
                        
                        else:
                            # Try as plain text
                            return await response.text()
                    
                    else:
                        logger.warning(f"HTTP {response.status} when fetching {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error extracting from URL {url}: {e}")
            return None
    
    
    async def _analyze_custom_content(
        self, 
        content: str, 
        source: CustomSource, 
        startup_info: Any
    ) -> Dict[str, Any]:
        """Enhanced analysis of custom content with regional specialization and priority weighting"""
        
        # Detect if this is Pakistan-specific content for enhanced processing
        is_pakistan_focused = self._is_pakistan_regulatory_content(content, startup_info)
        is_robotics_focused = self._is_robotics_industry_content(content, startup_info)
        
        # Create specialized analysis prompt based on content type
        if is_pakistan_focused:
            analysis_prompt = self._create_pakistan_analysis_prompt(content, source, startup_info)
        elif is_robotics_focused:
            analysis_prompt = self._create_robotics_analysis_prompt(content, source, startup_info)
        else:
            analysis_prompt = self._create_general_analysis_prompt(content, source, startup_info)
        
        try:
            response = await gemini_client.generate_response(
                analysis_prompt,
                temperature=0.2,  # Lower temperature for more focused extraction
                system_prompt="You are a regulatory compliance expert specializing in Pakistan regulations and technology sector compliance. Extract specific, actionable requirements."
            )
            
            # Parse the AI response with enhanced validation
            analysis = await self._parse_content_analysis(response)
            
            # Apply priority weighting for user-provided sources
            analysis['priority_weight'] = self._calculate_priority_weight(source, is_pakistan_focused, is_robotics_focused)
            analysis['source_confidence'] = self._calculate_source_confidence(analysis, is_pakistan_focused)
            
            logger.info(f"Custom source analysis completed: {analysis.get('document_type', 'unknown')} with priority {analysis['priority_weight']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing custom content: {e}")
            return {
                "document_type": "unknown", 
                "confidence_score": 0.5,
                "priority_weight": 0.7,  # Default high priority for user sources
                "source_confidence": 0.5
            }

    def _is_pakistan_regulatory_content(self, content: str, startup_info: Any) -> bool:
        """Detect if content is Pakistan-specific regulatory information"""
        content_lower = content.lower()
        pakistan_indicators = [
            'pakistan', 'secp', 'securities and exchange commission of pakistan',
            'federal board of revenue', 'fbr', 'pta', 'pakistan telecommunications authority',
            'psqca', 'pakistan standards', 'state bank of pakistan', 'sbp',
            'karachi', 'lahore', 'islamabad', 'pakistani law', 'pakistan government',
            'ministry of commerce', 'ministry of industries', 'federal ministry'
        ]
        
        # Check if Pakistan is mentioned in startup context and content has Pakistani indicators
        pakistan_in_context = any('pakistan' in country.lower() for country in startup_info.target_countries)
        pakistan_in_content = any(indicator in content_lower for indicator in pakistan_indicators)
        
        return pakistan_in_context and pakistan_in_content

    def _is_robotics_industry_content(self, content: str, startup_info: Any) -> bool:
        """Detect if content is robotics/hardware industry specific"""
        content_lower = content.lower()
        robotics_indicators = [
            'robot', 'robotic', 'robotics', 'automation', 'manufacturing',
            'hardware', 'electronics', 'iot', 'sensors', 'actuators',
            'industrial automation', 'mechatronics', 'embedded systems',
            'product certification', 'type approval', 'safety standards'
        ]
        
        robotics_in_context = any(term in startup_info.industry.lower() for term in ['robot', 'hardware', 'manufacturing'])
        robotics_in_content = any(indicator in content_lower for indicator in robotics_indicators)
        
        return robotics_in_context and robotics_in_content

    def _create_pakistan_analysis_prompt(self, content: str, source: CustomSource, startup_info: Any) -> str:
        """Create specialized prompt for Pakistan regulatory content"""
        return f"""
        PRIORITY ANALYSIS: Pakistan Regulatory Document for {startup_info.industry} Startup
        
        USER PROVIDED SOURCE: {source.title or source.source_name or 'Legal Resource Guide'}
        User Description: {source.description or source.user_description or 'Pakistan legal/regulatory document'}
        
        TARGET STARTUP CONTEXT:
        - Industry: {startup_info.industry} (Focus on this sector)
        - Primary Country: Pakistan  
        - Business Activities: {startup_info.business_activities}
        - Stage: {getattr(startup_info, 'stage', 'startup')}
        
        DOCUMENT CONTENT (Analyzing first 4000 chars for Pakistan-specific regulations):
        {content[:4000]}
        
        PAKISTAN REGULATORY FOCUS AREAS:
        1. SECP (Securities & Exchange Commission) - Business registration, corporate compliance
        2. PTA (Pakistan Telecommunications Authority) - Technology/electronics approval  
        3. FBR (Federal Board of Revenue) - Tax obligations, customs, import duties
        4. PSQCA (Pakistan Standards & Quality Control) - Product standards, certification
        5. SBP (State Bank of Pakistan) - Financial services, fintech regulations
        6. Ministry of Industries & Production - Manufacturing licenses
        7. Provincial regulations - Punjab, Sindh, KPK, Balochistan specific rules
        
        EXTRACT SPECIFICALLY FOR {startup_info.industry.upper()} STARTUPS IN PAKISTAN:
        - Business registration requirements with SECP
        - Industry-specific licenses needed
        - Product/service approval processes (especially PTA if technology-related)
        - Tax registration requirements (NTN, STN, sales tax)
        - Import/export regulations for components
        - Employment and labor law compliance
        - Environmental clearances if manufacturing
        - Intellectual property protection requirements
        
        Be EXTREMELY SPECIFIC about Pakistan requirements. Extract regulation numbers, required documents, fees, timelines.
        """

    def _create_robotics_analysis_prompt(self, content: str, source: CustomSource, startup_info: Any) -> str:
        """Create specialized prompt for robotics/hardware industry content"""
        return f"""
        SPECIALIZED ANALYSIS: Robotics/Hardware Industry Compliance Document
        
        USER PROVIDED SOURCE: {source.title or source.source_name}
        Description: {source.description or source.user_description or 'Robotics/Hardware industry regulatory document'}
        
        ROBOTICS STARTUP CONTEXT:
        - Industry: {startup_info.industry} 
        - Target Markets: {startup_info.target_countries}
        - Activities: {startup_info.business_activities}
        
        DOCUMENT CONTENT:
        {content[:4000]}
        
        ROBOTICS/HARDWARE SPECIFIC COMPLIANCE AREAS:
        1. Product Safety & Standards - CE marking, ISO standards, safety certifications
        2. Electronics Approval - FCC, IC, PTA type approval for wireless devices
        3. Manufacturing Standards - Quality management, production facility requirements
        4. Import/Export Controls - Component sourcing, customs classifications
        5. Intellectual Property - Patent protection, design rights
        6. Liability & Insurance - Product liability, professional indemnity
        7. Data Privacy - If robots collect data, GDPR/local privacy laws apply
        8. Employment - Skilled worker visas, technical staff requirements
        
        EXTRACT ROBOTICS-SPECIFIC REQUIREMENTS:
        - Product certification processes and standards
        - Electronics/wireless device approvals
        - Manufacturing facility licensing
        - Import duties and customs procedures for components
        - Safety and liability requirements
        - Technical standards compliance (ISO, IEC, etc.)
        
        Focus on actionable requirements for robotics hardware manufacturing and deployment.
        """

    def _create_general_analysis_prompt(self, content: str, source: CustomSource, startup_info: Any) -> str:
        """Create general analysis prompt for other types of documents"""
        return f"""
        COMPREHENSIVE REGULATORY ANALYSIS: User-Provided Legal Document
        
        USER SOURCE DETAILS:
        - Name: {source.title or source.source_name or 'User Document'}
        - Description: {source.description or source.user_description or 'Legal/regulatory document'}
        - User Notes: {source.relevance_note or 'User believes this is relevant'}
        
        STARTUP CONTEXT:
        - Industry: {startup_info.industry}
        - Countries: {', '.join(startup_info.target_countries)}
        - Activities: {startup_info.business_activities}
        - Data Handling: {getattr(startup_info, 'data_handling', [])}
        
        DOCUMENT CONTENT:
        {content[:3500]}
        
        COMPREHENSIVE ANALYSIS REQUIRED:
        1. Document Classification - What type of legal/regulatory document is this?
        2. Jurisdiction Analysis - Which countries/regions does this apply to?
        3. Industry Relevance - How does this apply to the {startup_info.industry} industry?
        4. Compliance Requirements - What specific actions must the startup take?
        5. Implementation Timeline - Are there deadlines or phased requirements?
        6. Penalties/Consequences - What happens for non-compliance?
        7. Related Regulations - Are there connected requirements mentioned?
        
        EXTRACT ACTIONABLE REQUIREMENTS:
        - Specific compliance obligations for this startup
        - Required documentation, licenses, or registrations
        - Implementation steps and timelines
        - Costs, fees, or financial requirements
        - Ongoing obligations (reporting, renewals, etc.)
        
        Since this is USER-PROVIDED, treat as HIGH PRIORITY and extract maximum detail.
        """

    def _calculate_priority_weight(self, source: CustomSource, is_pakistan_focused: bool, is_robotics_focused: bool) -> float:
        """Calculate priority weight for user-provided sources"""
        base_weight = 0.9  # User sources start with high priority
        
        # Boost for contextual relevance
        if is_pakistan_focused:
            base_weight += 0.05
        if is_robotics_focused:
            base_weight += 0.05
        
        # Boost if user provided description/relevance notes
        if source.description or source.user_description:
            base_weight += 0.02
        if source.relevance_note:
            base_weight += 0.02
        
        return min(1.0, base_weight)

    def _calculate_source_confidence(self, analysis: Dict[str, Any], is_specialized: bool) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.7  # Default for user sources
        
        # Boost confidence if we found specific regulatory information
        if analysis.get('regulation_ids'):
            base_confidence += 0.1
        if analysis.get('authority'):
            base_confidence += 0.1
        if len(analysis.get('key_requirements', [])) > 3:
            base_confidence += 0.05
        if is_specialized:  # Pakistan or robotics focused
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    async def _parse_content_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI analysis response into structured data"""
        
        # Use AI to extract structured data from the analysis
        extraction_prompt = f"""
        Extract structured data from this regulatory document analysis:
        
        {response}
        
        Return a JSON object with:
        {{
            "document_type": "regulation|guidance|proposal|legal_document",
            "authority": "issuing authority name or null",
            "regulation_ids": ["list", "of", "regulation", "references"],
            "key_requirements": ["list", "of", "main", "compliance", "requirements"],
            "confidence_score": 0.0-1.0,
            "implementation_actions": ["specific", "actions", "startup", "needs"]
        }}
        
        Return ONLY the JSON object.
        """
        
        try:
            structured_response = await gemini_client.generate_response(
                extraction_prompt,
                temperature=0.1
            )
            
            # Parse JSON response
            import json
            clean_response = structured_response.strip().strip('```json').strip('```').strip()
            
            analysis_data = json.loads(clean_response)
            
            # Validate and clean the data
            return {
                "document_type": analysis_data.get("document_type", "unknown"),
                "authority": analysis_data.get("authority"),
                "regulation_ids": analysis_data.get("regulation_ids", []),
                "key_requirements": analysis_data.get("key_requirements", []),
                "confidence_score": min(max(analysis_data.get("confidence_score", 0.5), 0.0), 1.0),
                "implementation_actions": analysis_data.get("implementation_actions", [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing content analysis: {e}")
            return {
                "document_type": "unknown",
                "authority": None,
                "regulation_ids": [],
                "key_requirements": [],
                "confidence_score": 0.5,
                "implementation_actions": []
            }
    
    def convert_to_regulatory_documents(
        self, 
        processed_sources: List[ProcessedCustomSource]
    ) -> List[Dict]:
        """Convert processed custom sources to regulatory document format with priority weighting"""
        
        regulatory_docs = []
        
        for source in processed_sources:
            # Enhanced priority calculation based on analysis
            base_priority = getattr(source, 'priority_weight', 0.9)
            source_confidence = getattr(source, 'source_confidence', 0.8)
            
            # Create enhanced regulatory document
            doc = {
                "title": self._create_enhanced_title(source),
                "content": source.extracted_content,
                "source": source.authority or "User-Provided High Priority Source",
                "country": self._determine_document_country(source),
                "regulation_type": self._normalize_document_type(source.document_type),
                "url": getattr(source.original_source, 'url', source.original_source.content) if source.original_source.type == 'url' else '',
                "authority": source.authority or self._infer_authority(source),
                "regulation_id": self._format_regulation_ids(source.regulation_ids),
                "citation_format": self._create_citation_format(source),
                
                # Enhanced priority and relevance
                "relevance_score": min(0.98, base_priority + 0.08),  # User sources get very high relevance
                "priority_weight": base_priority,
                "source_confidence": source_confidence,
                
                # Custom source specific fields
                "user_provided": True,
                "user_description": source.original_source.description or source.original_source.user_description,
                "user_relevance_note": source.original_source.relevance_note,
                "key_requirements": source.key_requirements,
                "processing_notes": f"Enhanced analysis applied - Priority: {base_priority:.2f}",
                
                # Quality indicators
                "extraction_quality": "enhanced" if base_priority > 0.85 else "standard",
                "context_match": "high" if self._has_context_match(source) else "medium"
            }
            
            regulatory_docs.append(doc)
            logger.info(f"Converted custom source: {doc['title']} (Priority: {base_priority:.2f}, Relevance: {doc['relevance_score']:.2f})")
        
        # Sort by priority weight (highest first) 
        regulatory_docs.sort(key=lambda x: x['priority_weight'], reverse=True)
        
        logger.info(f"Custom source conversion completed: {len(regulatory_docs)} documents with enhanced prioritization")
        return regulatory_docs

    def _create_enhanced_title(self, source: ProcessedCustomSource) -> str:
        """Create enhanced title for the document"""
        # Try multiple sources for the title
        original_name = (source.original_source.title or 
                        source.original_source.source_name or 
                        source.original_source.description)
        doc_type = source.document_type.replace('_', ' ').title()
        
        if original_name and original_name.lower() not in ['unnamed source', '']:
            return f"[USER] {original_name}"
        else:
            return f"[USER] {doc_type} - {source.authority or 'Regulatory Document'}"

    def _determine_document_country(self, source: ProcessedCustomSource) -> str:
        """Determine the country/jurisdiction of the document"""
        content_lower = source.extracted_content.lower()
        
        # Check for specific country indicators in content
        country_indicators = {
            'Pakistan': ['pakistan', 'secp', 'fbr', 'pta', 'psqca', 'karachi', 'lahore', 'islamabad'],
            'India': ['india', 'indian', 'rbi', 'sebi', 'delhi', 'mumbai'],
            'Germany': ['germany', 'german', 'bafin', 'bundesbank', 'berlin'],
            'United States': ['usa', 'united states', 'sec', 'fda', 'fcc'],
            'United Kingdom': ['uk', 'united kingdom', 'fca', 'london'],
            'European Union': ['european union', 'eu', 'gdpr', 'european commission']
        }
        
        for country, indicators in country_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return country
        
        return "User-Specified"

    def _normalize_document_type(self, doc_type: str) -> str:
        """Normalize document type for consistency"""
        type_mapping = {
            'legal_document': 'legal_guidance',
            'proposal': 'regulatory_proposal', 
            'unknown': 'regulatory_document'
        }
        return type_mapping.get(doc_type, doc_type)

    def _infer_authority(self, source: ProcessedCustomSource) -> str:
        """Infer the issuing authority if not explicitly found"""
        content_lower = source.extracted_content.lower()
        
        authorities = {
            'Securities & Exchange Commission of Pakistan (SECP)': ['secp', 'securities exchange commission pakistan'],
            'Pakistan Telecommunications Authority (PTA)': ['pta', 'pakistan telecommunications'],
            'Federal Board of Revenue (FBR)': ['fbr', 'federal board revenue'],
            'Pakistan Standards & Quality Control Authority (PSQCA)': ['psqca', 'standards quality'],
            'State Bank of Pakistan (SBP)': ['sbp', 'state bank pakistan'],
            'European Commission': ['european commission', 'ec.europa.eu'],
            'German Federal Financial Supervisory Authority (BaFin)': ['bafin', 'bundesanstalt'],
        }
        
        for authority, indicators in authorities.items():
            if any(indicator in content_lower for indicator in indicators):
                return authority
        
        return "Regulatory Authority"

    def _format_regulation_ids(self, regulation_ids: List[str]) -> str:
        """Format regulation IDs into a readable string"""
        if not regulation_ids:
            return "See document content"
        
        # Clean and format regulation IDs
        cleaned_ids = [rid.strip() for rid in regulation_ids if rid.strip()]
        return ", ".join(cleaned_ids[:5])  # Limit to 5 most important IDs

    def _create_citation_format(self, source: ProcessedCustomSource) -> str:
        """Create proper citation format for the source"""
        title = (source.original_source.title or 
                source.original_source.source_name or 
                "User-Provided Document")
        authority = source.authority or "User Source"
        
        if source.original_source.type == 'url':
            url_content = getattr(source.original_source, 'url', source.original_source.content)
            return f"{authority}, \"{title}\", Available at: {url_content}"
        else:
            return f"{authority}, \"{title}\" (User-Provided Document)"

    def _has_context_match(self, source: ProcessedCustomSource) -> bool:
        """Check if the source has good context match with startup info"""
        # High context match if we found specific requirements or authority info
        return (len(source.key_requirements) > 2 or 
                source.authority is not None or 
                len(source.regulation_ids) > 0)

# Global custom source agent
custom_source_agent = CustomSourceAgent() 