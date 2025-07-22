"""
Enhanced Data Models with Source Tracking and Citation Support
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SourceType(str, Enum):
    """Types of sources for regulatory information"""
    OFFICIAL_REGULATION = "official_regulation"
    GOVERNMENT_WEBSITE = "government_website"
    LEGAL_DATABASE = "legal_database"
    AI_GENERATED = "ai_generated"
    CACHED_ANALYSIS = "cached_analysis"
    THIRD_PARTY = "third_party"

class SourceQuality(str, Enum):
    """Quality assessment of sources"""
    PRIMARY = "primary"      # Official government/regulatory text
    SECONDARY = "secondary"  # Legal databases, official summaries
    TERTIARY = "tertiary"    # Third-party analysis, interpretations
    AI_INFERRED = "ai_inferred"  # AI-generated content
    UNKNOWN = "unknown"      # Quality cannot be determined

class RegulatorySource(BaseModel):
    """Enhanced source information with quality tracking"""
    url: Optional[str] = None
    title: str
    authority: Optional[str] = None  # e.g., "BaFin", "SEC", "European Commission"
    source_type: SourceType
    source_quality: SourceQuality
    last_accessed: Optional[datetime] = None
    last_updated: Optional[str] = None
    regulation_id: Optional[str] = None  # Official regulation number/ID
    section_reference: Optional[str] = None  # Specific section cited
    confidence_score: float = 0.0  # 0-1 confidence in source reliability
    is_current: bool = True  # Whether the source is current/valid
    
class Citation(BaseModel):
    """Proper citation for regulatory requirements"""
    source: RegulatorySource
    excerpt: Optional[str] = None  # Relevant text excerpt
    page_number: Optional[str] = None
    citation_format: str  # Formatted citation string
    relevance_score: float = 0.0  # How relevant this source is to the gap

class ComplianceGapWithSources(BaseModel):
    """Enhanced compliance gap with source tracking"""
    title: str
    gap_type: str
    severity: str
    description: str
    recommended_actions: List[str]
    country: str
    deadline: Optional[str] = None
    estimated_cost: Optional[str] = None
    
    # Enhanced source tracking
    primary_sources: List[Citation] = []  # Official regulations
    supporting_sources: List[Citation] = []  # Additional context
    ai_confidence: float = 0.0  # AI's confidence in this analysis
    source_coverage: float = 0.0  # % of requirements backed by sources
    missing_sources: List[str] = []  # Areas where sources couldn't be found
    
    def get_source_quality_score(self) -> float:
        """Calculate overall source quality for this gap"""
        if not self.primary_sources:
            return 0.0
        
        total_score = sum(s.source.confidence_score for s in self.primary_sources)
        return total_score / len(self.primary_sources)
    
    def has_sufficient_sources(self) -> bool:
        """Check if gap has sufficient source backing"""
        return (len(self.primary_sources) > 0 and 
                self.source_coverage >= 0.7 and 
                self.get_source_quality_score() >= 0.6)

class SourcedRegulatoryDocument(BaseModel):
    """Enhanced regulatory document with source metadata"""
    title: str
    content: str
    source: RegulatorySource
    country: str
    regulation_type: str
    relevance_score: float = 0.0
    
    # Content analysis
    key_requirements: List[str] = []
    penalties_mentioned: List[str] = []
    deadlines_mentioned: List[str] = []

class AnalysisQualityReport(BaseModel):
    """Quality assessment of the entire analysis"""
    total_gaps: int
    gaps_with_sources: int
    gaps_without_sources: int
    average_source_quality: float
    primary_source_coverage: float  # % gaps backed by primary sources
    confidence_score: float
    missing_source_areas: List[str]
    recommendations: List[str]  # What to do about missing sources 