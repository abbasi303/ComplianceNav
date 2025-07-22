"""
Citation Manager for Regulatory Compliance Sources
Handles source tracking, citation generation, and quality assessment
"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from loguru import logger

from core.data_models import (
    RegulatorySource, Citation, SourceType, SourceQuality, 
    ComplianceGapWithSources, AnalysisQualityReport
)

class CitationManager:
    """Manages source tracking and citation generation for compliance analysis"""
    
    def __init__(self):
        self.source_cache: Dict[str, RegulatorySource] = {}
        self.authority_patterns = {
            'BaFin': ['bafin.de', 'bundesanstalt', 'financial supervisory'],
            'SEC': ['sec.gov', 'securities exchange commission'],
            'European Commission': ['europa.eu', 'european commission', 'ec.europa.eu'],
            'FinCEN': ['fincen.gov', 'financial crimes enforcement'],
            'FCA': ['fca.org.uk', 'financial conduct authority'],
            'CFTC': ['cftc.gov', 'commodity futures trading'],
        }
        
    def create_source_from_document(self, doc_data: dict) -> RegulatorySource:
        """Create a RegulatorySource from document metadata"""
        try:
            # Determine source type and quality
            source_type = self._determine_source_type(doc_data.get('url', ''), doc_data.get('source', ''))
            source_quality = self._assess_source_quality(doc_data.get('url', ''), doc_data.get('authority', ''))
            authority = self._identify_authority(doc_data.get('url', ''), doc_data.get('content', ''))
            
            source = RegulatorySource(
                url=doc_data.get('url'),
                title=doc_data.get('title', 'Unknown Document'),
                authority=authority,
                source_type=source_type,
                source_quality=source_quality,
                last_accessed=datetime.now() if doc_data.get('url') else None,
                last_updated=doc_data.get('last_updated'),
                regulation_id=self._extract_regulation_id(doc_data.get('content', '')),
                confidence_score=self._calculate_confidence_score(source_type, source_quality, authority),
                is_current=True  # Assume current unless proven otherwise
            )
            
            # Cache the source
            cache_key = f"{source.title}_{source.authority}_{source.url}"
            self.source_cache[cache_key] = source
            
            return source
            
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            return self._create_fallback_source(doc_data)
    
    def generate_citation(self, source: RegulatorySource, excerpt: Optional[str] = None) -> Citation:
        """Generate a properly formatted citation"""
        try:
            # Create citation format based on source type
            if source.source_quality == SourceQuality.PRIMARY:
                citation_format = self._format_primary_citation(source)
            elif source.source_quality == SourceQuality.SECONDARY:
                citation_format = self._format_secondary_citation(source)
            else:
                citation_format = self._format_general_citation(source)
            
            return Citation(
                source=source,
                excerpt=excerpt[:500] if excerpt else None,  # Limit excerpt length
                citation_format=citation_format,
                relevance_score=0.8 if source.source_quality in [SourceQuality.PRIMARY, SourceQuality.SECONDARY] else 0.5
            )
            
        except Exception as e:
            logger.error(f"Error generating citation: {e}")
            return Citation(
                source=source,
                citation_format=f"{source.title} ({source.authority or 'Unknown Authority'})",
                relevance_score=0.3
            )
    
    def assess_gap_source_quality(self, gap: ComplianceGapWithSources) -> Dict[str, any]:
        """Assess the source quality for a compliance gap"""
        try:
            total_sources = len(gap.primary_sources) + len(gap.supporting_sources)
            primary_count = len(gap.primary_sources)
            
            if total_sources == 0:
                return {
                    'quality_score': 0.0,
                    'confidence': 'Very Low',
                    'recommendations': ['Find official regulatory sources', 'Consult legal expert'],
                    'warning': 'No sources provided - analysis may be incomplete'
                }
            
            # Calculate quality metrics
            avg_confidence = sum(c.source.confidence_score for c in gap.primary_sources + gap.supporting_sources) / total_sources
            primary_ratio = primary_count / total_sources if total_sources > 0 else 0
            
            quality_score = (avg_confidence * 0.6) + (primary_ratio * 0.4)
            
            # Determine confidence level and recommendations
            if quality_score >= 0.8 and primary_count >= 2:
                confidence = 'High'
                recommendations = ['Sources appear comprehensive']
            elif quality_score >= 0.6 and primary_count >= 1:
                confidence = 'Medium'
                recommendations = ['Consider additional primary sources', 'Verify with legal counsel']
            elif quality_score >= 0.4:
                confidence = 'Low'
                recommendations = ['Seek official regulatory sources', 'Consult legal expert', 'Verify all requirements']
            else:
                confidence = 'Very Low'
                recommendations = ['Analysis incomplete', 'Obtain primary regulatory sources', 'Professional legal review required']
            
            warning = None
            if primary_count == 0:
                warning = 'No primary sources - recommendations based on secondary/tertiary sources only'
            elif gap.source_coverage < 0.5:
                warning = f'Low source coverage ({gap.source_coverage:.0%}) - some requirements may be missing'
                
            return {
                'quality_score': quality_score,
                'confidence': confidence,
                'recommendations': recommendations,
                'warning': warning,
                'primary_sources': primary_count,
                'total_sources': total_sources
            }
            
        except Exception as e:
            logger.error(f"Error assessing gap source quality: {e}")
            return {
                'quality_score': 0.0,
                'confidence': 'Unknown',
                'recommendations': ['Source quality assessment failed'],
                'warning': 'Unable to assess source quality'
            }
    
    def generate_analysis_quality_report(self, gaps: List[ComplianceGapWithSources]) -> AnalysisQualityReport:
        """Generate overall quality report for the analysis"""
        try:
            total_gaps = len(gaps)
            gaps_with_sources = sum(1 for gap in gaps if gap.primary_sources or gap.supporting_sources)
            gaps_without_sources = total_gaps - gaps_with_sources
            
            # Calculate average source quality
            quality_scores = []
            primary_source_count = 0
            missing_areas = []
            
            for gap in gaps:
                assessment = self.assess_gap_source_quality(gap)
                quality_scores.append(assessment['quality_score'])
                
                if assessment['primary_sources'] > 0:
                    primary_source_count += 1
                    
                if assessment['warning']:
                    missing_areas.append(f"{gap.title}: {assessment['warning']}")
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            primary_coverage = primary_source_count / total_gaps if total_gaps > 0 else 0.0
            
            # Generate recommendations
            recommendations = []
            if gaps_without_sources > 0:
                recommendations.append(f"Obtain sources for {gaps_without_sources} unsourced compliance gaps")
            if primary_coverage < 0.7:
                recommendations.append("Increase primary source coverage - seek official regulations")
            if avg_quality < 0.6:
                recommendations.append("Overall source quality is low - professional legal review recommended")
                
            return AnalysisQualityReport(
                total_gaps=total_gaps,
                gaps_with_sources=gaps_with_sources,
                gaps_without_sources=gaps_without_sources,
                average_source_quality=avg_quality,
                primary_source_coverage=primary_coverage,
                confidence_score=avg_quality * primary_coverage,
                missing_source_areas=missing_areas[:10],  # Limit to top 10
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return AnalysisQualityReport(
                total_gaps=len(gaps),
                gaps_with_sources=0,
                gaps_without_sources=len(gaps),
                average_source_quality=0.0,
                primary_source_coverage=0.0,
                confidence_score=0.0,
                missing_source_areas=["Quality assessment failed"],
                recommendations=["Unable to assess source quality - manual review required"]
            )
    
    def _determine_source_type(self, url: str, source_description: str) -> SourceType:
        """Determine the type of source based on URL and description"""
        if not url:
            return SourceType.AI_GENERATED
            
        url_lower = url.lower()
        desc_lower = source_description.lower()
        
        # Government/official sites
        if any(domain in url_lower for domain in ['.gov', '.eu', 'europa.eu', 'bundesbank.de']):
            return SourceType.OFFICIAL_REGULATION
        
        # Legal databases
        if any(domain in url_lower for domain in ['westlaw', 'lexis', 'justia', 'law.', 'legal']):
            return SourceType.LEGAL_DATABASE
            
        # Check description for indicators
        if any(term in desc_lower for term in ['official', 'regulation', 'directive', 'act']):
            return SourceType.GOVERNMENT_WEBSITE
            
        return SourceType.THIRD_PARTY
    
    def _assess_source_quality(self, url: str, authority: str) -> SourceQuality:
        """Assess the quality of a source"""
        if not url and not authority:
            return SourceQuality.AI_INFERRED
            
        url_lower = url.lower() if url else ""
        auth_lower = authority.lower() if authority else ""
        
        # Primary sources - official government/regulatory
        if any(domain in url_lower for domain in ['.gov', 'europa.eu', 'bafin.de', 'sec.gov']):
            return SourceQuality.PRIMARY
            
        # Secondary sources - legal databases, official summaries
        if any(domain in url_lower for domain in ['westlaw', 'lexis', 'official']):
            return SourceQuality.SECONDARY
            
        # Check authority
        if any(auth in auth_lower for auth in ['bafin', 'sec', 'european commission']):
            return SourceQuality.PRIMARY
            
        return SourceQuality.TERTIARY
    
    def _identify_authority(self, url: str, content: str) -> Optional[str]:
        """Identify the regulatory authority from URL and content"""
        text_to_check = f"{url} {content}".lower()
        
        for authority, patterns in self.authority_patterns.items():
            if any(pattern in text_to_check for pattern in patterns):
                return authority
                
        return None
    
    def _extract_regulation_id(self, content: str) -> Optional[str]:
        """Extract regulation ID/number from content"""
        # Common patterns for regulation IDs
        patterns = [
            r'Directive (\d{4}/\d+/EC)',
            r'Regulation \(EU\) (\d{4}/\d+)',
            r'§\s*(\d+[a-z]?)',
            r'Article (\d+)',
            r'Section (\d+)',
            r'([A-Z]{2,}\s*\d{4}-\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
                
        return None
    
    def _calculate_confidence_score(self, source_type: SourceType, source_quality: SourceQuality, authority: Optional[str]) -> float:
        """Calculate confidence score for a source"""
        base_score = 0.3
        
        # Source type bonus
        type_scores = {
            SourceType.OFFICIAL_REGULATION: 0.4,
            SourceType.GOVERNMENT_WEBSITE: 0.3,
            SourceType.LEGAL_DATABASE: 0.2,
            SourceType.THIRD_PARTY: 0.1,
            SourceType.AI_GENERATED: 0.0,
            SourceType.CACHED_ANALYSIS: 0.1
        }
        
        # Quality bonus
        quality_scores = {
            SourceQuality.PRIMARY: 0.3,
            SourceQuality.SECONDARY: 0.2,
            SourceQuality.TERTIARY: 0.1,
            SourceQuality.AI_INFERRED: 0.0,
            SourceQuality.UNKNOWN: 0.05
        }
        
        # Authority bonus
        authority_bonus = 0.1 if authority else 0.0
        
        return min(1.0, base_score + type_scores.get(source_type, 0) + quality_scores.get(source_quality, 0) + authority_bonus)
    
    def _format_primary_citation(self, source: RegulatorySource) -> str:
        """Format citation for primary sources"""
        parts = []
        
        if source.authority:
            parts.append(f"{source.authority}")
        
        parts.append(f"\"{source.title}\"")
        
        if source.regulation_id:
            parts.append(f"({source.regulation_id})")
            
        if source.last_updated:
            parts.append(f"last updated {source.last_updated}")
            
        if source.url:
            parts.append(f"Available at: {source.url}")
            
        return ", ".join(parts)
    
    def _format_secondary_citation(self, source: RegulatorySource) -> str:
        """Format citation for secondary sources"""
        return f"\"{source.title}\" ({source.authority or 'Secondary Source'}){f', {source.url}' if source.url else ''}"
    
    def _format_general_citation(self, source: RegulatorySource) -> str:
        """Format general citation"""
        return f"{source.title}{f' ({source.authority})' if source.authority else ''}{f', {source.url}' if source.url else ''}"
    
    def _create_fallback_source(self, doc_data: dict) -> RegulatorySource:
        """Create a fallback source when normal creation fails"""
        return RegulatorySource(
            title=doc_data.get('title', 'Unknown Source'),
            authority=doc_data.get('authority'),
            source_type=SourceType.AI_GENERATED,
            source_quality=SourceQuality.AI_INFERRED,
            confidence_score=0.3,
            is_current=True
        )

# Global citation manager instance
citation_manager = CitationManager() 