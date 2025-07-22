"""
Pakistan Regulatory Module - Enhanced Knowledge Base
Specialized module for Pakistan regulatory compliance with detailed authority mapping
"""

from typing import Dict, List, Any
from loguru import logger
from agents.regional_regulatory_agent import CountryModule
from core.data_models import RegulatoryDocument
from integrations.gemini_client import gemini_client

class PakistanRegulatoryModule(CountryModule):
    """
    Pakistan-specific regulatory module with detailed authority knowledge
    Covers SECP, PTA, FBR, PSQCA, SBP, and provincial requirements
    """
    
    def __init__(self):
        super().__init__("Pakistan")
        self.version = "1.0"
        self._initialize_pakistan_authorities()
        self._initialize_regulation_patterns()
        self._initialize_industry_mappings()
        
        logger.info(f"Pakistan Regulatory Module initialized with {len(self.authorities)} authorities")
    
    def _initialize_pakistan_authorities(self):
        """Initialize Pakistan-specific regulatory authorities"""
        self.authorities = {
            'business_registration': 'Securities and Exchange Commission of Pakistan (SECP)',
            'tax_authority': 'Federal Board of Revenue (FBR)', 
            'telecommunications': 'Pakistan Telecommunications Authority (PTA)',
            'standards_quality': 'Pakistan Standards and Quality Control Authority (PSQCA)',
            'financial_services': 'State Bank of Pakistan (SBP)',
            'manufacturing': 'Ministry of Industries and Production',
            'labor_employment': 'Ministry of Labour and Manpower',
            'environment': 'Pakistan Environmental Protection Agency (EPA)',
            'customs_import': 'Pakistan Customs (under FBR)',
            'intellectual_property': 'Intellectual Property Organization of Pakistan (IPO)',
            'food_safety': 'Pakistan Food Authority (PFA)',
            'drug_regulation': 'Drug Regulatory Authority of Pakistan (DRAP)',
        }
    
    def _initialize_regulation_patterns(self):
        """Initialize Pakistan-specific regulation patterns and requirements"""
        self.regulation_patterns = {
            'company_incorporation': {
                'authority': 'SECP',
                'documents': ['Incorporation Application', 'Memorandum of Association', 'Articles of Association'],
                'fees': 'PKR 2,000 - 10,000 (depending on capital)',
                'timeline': '7-15 business days',
                'legal_basis': 'Companies Act 2017'
            },
            'ntn_registration': {
                'authority': 'FBR', 
                'documents': ['CNIC/Passport', 'Business Registration Certificate'],
                'fees': 'Free',
                'timeline': '1-3 business days',
                'legal_basis': 'Income Tax Ordinance 2001'
            },
            'pta_equipment_approval': {
                'authority': 'PTA',
                'documents': ['Type Approval Application', 'Technical Specifications', 'Test Reports'],
                'fees': 'PKR 50,000 - 200,000',
                'timeline': '30-45 business days',
                'legal_basis': 'Pakistan Telecommunication (Re-organization) Act 1996'
            },
            'manufacturing_license': {
                'authority': 'Provincial Government',
                'documents': ['Factory License Application', 'Layout Plan', 'Environmental Clearance'],
                'fees': 'PKR 10,000 - 50,000',
                'timeline': '30-60 business days',
                'legal_basis': 'Factories Act 1934'
            }
        }
    
    def _initialize_industry_mappings(self):
        """Initialize industry-specific regulatory requirements for Pakistan"""
        self.industry_mappings = {
            'robotics': [
                'company_incorporation',
                'ntn_registration', 
                'pta_equipment_approval',
                'manufacturing_license',
                'import_export_license',
                'worker_safety_compliance'
            ],
            'fintech': [
                'company_incorporation',
                'ntn_registration',
                'sbp_approval',
                'anti_money_laundering',
                'data_protection'
            ],
            'software': [
                'company_incorporation', 
                'ntn_registration',
                'pseb_registration',
                'export_incentives'
            ],
            'manufacturing': [
                'company_incorporation',
                'ntn_registration',
                'manufacturing_license',
                'environmental_clearance',
                'worker_safety_compliance'
            ]
        }
    
    async def research_regulations(self, industry: str, business_activities: List[str], startup_info: Any) -> List[RegulatoryDocument]:
        """Research Pakistan-specific regulations with detailed authority knowledge"""
        
        logger.info(f"Pakistan Module: Researching regulations for {industry} industry")
        
        regulations = []
        
        # Step 1: Get industry-specific regulation patterns
        industry_key = self._normalize_industry(industry)
        priority_regs = self.get_priority_regulations(industry_key)
        
        # Step 2: Generate detailed regulatory documents for each priority regulation
        for reg_pattern in priority_regs:
            if reg_pattern in self.regulation_patterns:
                reg_doc = await self._create_detailed_regulation(reg_pattern, industry, startup_info)
                if reg_doc:
                    regulations.append(reg_doc)
        
        # Step 3: Add Pakistan-specific requirements based on business activities
        activity_regs = await self._research_activity_specific_regulations(business_activities, startup_info)
        regulations.extend(activity_regs)
        
        # Step 4: Add export/import regulations if applicable
        if self._needs_import_export_regs(business_activities):
            import_export_regs = await self._research_import_export_regulations(startup_info)
            regulations.extend(import_export_regs)
        
        logger.info(f"Pakistan Module: Generated {len(regulations)} detailed regulations")
        return regulations
    
    async def _create_detailed_regulation(self, reg_pattern: str, industry: str, startup_info: Any) -> RegulatoryDocument:
        """Create detailed regulation document based on Pakistan-specific pattern"""
        
        pattern_info = self.regulation_patterns[reg_pattern]
        
        # Generate detailed content using Pakistan-specific knowledge
        content_prompt = f"""
        Create detailed compliance guidance for {reg_pattern} in Pakistan for a {industry} startup.
        
        Authority: {pattern_info['authority']}
        Legal Basis: {pattern_info['legal_basis']}
        Required Documents: {', '.join(pattern_info['documents'])}
        Fees: {pattern_info['fees']}
        Processing Time: {pattern_info['timeline']}
        
        Provide detailed step-by-step process including:
        1. Eligibility criteria
        2. Required documentation with specifics
        3. Application process and where to apply
        4. Fees and payment methods
        5. Processing timeline and follow-up
        6. Common issues and how to avoid them
        7. Penalties for non-compliance
        
        Make this specific to Pakistan regulations and processes.
        """
        
        try:
            detailed_content = await gemini_client.generate_response(
                content_prompt,
                temperature=0.1,
                system_prompt="You are a Pakistan regulatory compliance expert. Provide accurate, actionable guidance."
            )
            
            title = self._generate_regulation_title(reg_pattern)
            
            return RegulatoryDocument(
                title=title,
                content=detailed_content,
                source=pattern_info['authority'],
                country="Pakistan",
                regulation_type=self._get_regulation_type(reg_pattern),
                authority=pattern_info['authority'],
                regulation_id=pattern_info['legal_basis'],
                citation_format=f"{pattern_info['authority']}, {title}",
                relevance_score=0.95  # High relevance for Pakistan-specific modules
            )
            
        except Exception as e:
            logger.error(f"Error creating detailed regulation for {reg_pattern}: {e}")
            return None
    
    async def _research_activity_specific_regulations(self, activities: List[str], startup_info: Any) -> List[RegulatoryDocument]:
        """Research regulations specific to business activities"""
        
        activity_regulations = []
        
        for activity in activities:
            activity_lower = activity.lower()
            
            # Manufacturing-specific regulations
            if 'manufacturing' in activity_lower or 'production' in activity_lower:
                manufacturing_regs = await self._get_manufacturing_regulations()
                activity_regulations.extend(manufacturing_regs)
            
            # Import/Export specific regulations  
            if 'import' in activity_lower or 'export' in activity_lower:
                trade_regs = await self._get_trade_regulations()
                activity_regulations.extend(trade_regs)
            
            # Technology/Software specific regulations
            if 'software' in activity_lower or 'technology' in activity_lower:
                tech_regs = await self._get_technology_regulations()
                activity_regulations.extend(tech_regs)
        
        return activity_regulations
    
    async def _get_manufacturing_regulations(self) -> List[RegulatoryDocument]:
        """Get Pakistan manufacturing-specific regulations"""
        
        manufacturing_regs = []
        
        # Factory License Requirements
        factory_license = RegulatoryDocument(
            title="Factory License - Pakistan Manufacturing Requirements",
            content="""
            Manufacturing License Requirements in Pakistan:
            
            Authority: Provincial Labor Department
            Legal Basis: Factories Act 1934
            
            Requirements:
            1. Factory layout plan approved by building authority
            2. Environmental clearance from EPA  
            3. Fire safety certificate from Fire Department
            4. Worker safety compliance plan
            5. Machinery installation certificate
            
            Application Process:
            1. Submit application to Provincial Labor Department
            2. Site inspection by labor inspector
            3. Compliance verification
            4. License issuance (valid for 1 year)
            
            Fees: PKR 10,000 - 50,000 (varies by province and factory size)
            Timeline: 30-60 business days
            
            Penalties: PKR 50,000 fine + closure for operating without license
            """,
            source="Provincial Labor Department",
            country="Pakistan", 
            regulation_type="manufacturing",
            authority="Provincial Labor Department",
            regulation_id="Factories Act 1934",
            citation_format="Factories Act 1934, Provincial Labor Department",
            relevance_score=0.9
        )
        
        manufacturing_regs.append(factory_license)
        return manufacturing_regs
    
    async def _get_trade_regulations(self) -> List[RegulatoryDocument]:
        """Get Pakistan import/export regulations"""
        
        trade_regs = []
        
        # Import/Export License
        trade_license = RegulatoryDocument(
            title="Import/Export License - Pakistan Trade Requirements",
            content="""
            Import/Export License Requirements in Pakistan:
            
            Authority: Ministry of Commerce / Pakistan Customs
            Legal Basis: Import Trade Policy & Export Trade Policy
            
            Requirements:
            1. Company registration with SECP
            2. NTN registration with FBR
            3. Bank account statement
            4. Chamber of Commerce membership
            
            Application Process:
            1. Online application through Ministry of Commerce portal
            2. Document submission and verification  
            3. License issuance (valid for 3 years)
            
            Special Requirements for Electronics:
            - PTA type approval for electronic equipment
            - PSQCA certification for quality standards
            - Environmental compliance certificate
            
            Fees: PKR 5,000 - 25,000 (depending on category)
            Timeline: 15-30 business days
            
            Benefits: Access to export incentives and duty exemptions
            """,
            source="Ministry of Commerce",
            country="Pakistan",
            regulation_type="trade",
            authority="Ministry of Commerce", 
            regulation_id="Import/Export Trade Policy",
            citation_format="Ministry of Commerce, Import/Export Trade Policy",
            relevance_score=0.9
        )
        
        trade_regs.append(trade_license)
        return trade_regs
    
    async def _get_technology_regulations(self) -> List[RegulatoryDocument]:
        """Get Pakistan technology sector regulations"""
        
        tech_regs = []
        
        # PSEB Registration for IT Companies
        pseb_reg = RegulatoryDocument(
            title="PSEB Registration - Pakistan Software Export Board",
            content="""
            PSEB Registration for IT/Software Companies:
            
            Authority: Pakistan Software Export Board (PSEB) 
            Legal Basis: IT Policy 2023
            
            Benefits of PSEB Registration:
            1. Tax exemptions and incentives
            2. Export financing support
            3. Skill development programs
            4. International certification assistance
            
            Requirements:
            1. Company registration with SECP
            2. Minimum 70% software/IT services revenue
            3. Qualified technical staff
            4. Business plan for export activities
            
            Application Process:
            1. Online registration through PSEB portal
            2. Document verification
            3. Site visit (if required)
            4. Certificate issuance
            
            Fees: PKR 10,000 - 50,000 (based on company size)
            Timeline: 15-30 business days
            
            Tax Benefits: 100% tax exemption on export income for first 3 years
            """,
            source="Pakistan Software Export Board (PSEB)",
            country="Pakistan",
            regulation_type="technology",
            authority="Pakistan Software Export Board (PSEB)",
            regulation_id="IT Policy 2023", 
            citation_format="PSEB, IT Policy 2023",
            relevance_score=0.85
        )
        
        tech_regs.append(pseb_reg)
        return tech_regs
    
    def _normalize_industry(self, industry: str) -> str:
        """Normalize industry name to match our mappings"""
        industry_lower = industry.lower()
        
        if 'robot' in industry_lower or 'automation' in industry_lower:
            return 'robotics'
        elif 'fintech' in industry_lower or 'financial' in industry_lower:
            return 'fintech'
        elif 'software' in industry_lower or 'app' in industry_lower:
            return 'software'
        elif 'manufactur' in industry_lower:
            return 'manufacturing'
        else:
            return 'general'
    
    def _needs_import_export_regs(self, activities: List[str]) -> bool:
        """Check if startup needs import/export regulations"""
        trade_keywords = ['import', 'export', 'international', 'global', 'components', 'supply chain']
        
        for activity in activities:
            if any(keyword in activity.lower() for keyword in trade_keywords):
                return True
        return False
    
    def _generate_regulation_title(self, reg_pattern: str) -> str:
        """Generate human-readable title for regulation pattern"""
        title_map = {
            'company_incorporation': 'Company Registration with SECP',
            'ntn_registration': 'National Tax Number (NTN) Registration',
            'pta_equipment_approval': 'PTA Equipment Type Approval',
            'manufacturing_license': 'Manufacturing License Requirements'
        }
        return title_map.get(reg_pattern, reg_pattern.replace('_', ' ').title())
    
    def _get_regulation_type(self, reg_pattern: str) -> str:
        """Get regulation type for pattern"""
        type_map = {
            'company_incorporation': 'business_registration',
            'ntn_registration': 'tax_compliance',
            'pta_equipment_approval': 'industry_specific',
            'manufacturing_license': 'licensing'
        }
        return type_map.get(reg_pattern, 'general')
    
    def get_authority_mapping(self) -> Dict[str, str]:
        """Get Pakistan authority mapping"""
        return self.authorities.copy()
    
    def get_priority_regulations(self, industry: str) -> List[str]:
        """Get priority regulations for specific industry"""
        return self.industry_mappings.get(industry, ['company_incorporation', 'ntn_registration'])
    
    async def _research_import_export_regulations(self, startup_info: Any) -> List[RegulatoryDocument]:
        """Research detailed import/export regulations"""
        return await self._get_trade_regulations() 