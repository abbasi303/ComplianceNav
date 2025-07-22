"""
Document Processing Module
Handles document validation, deduplication, and processing
Extracted from scout_agent.py for better modularity
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import hashlib

from agents.scout_agent import RegulatoryDocument

class DocumentProcessor:
    """Handles document processing and validation"""
    
    def __init__(self):
        self.name = "DocumentProcessor"
    
    def deduplicate_documents(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """Remove duplicate documents based on content similarity"""
        unique_docs = []
        seen_hashes = set()
        
        for doc in documents:
            # Create hash based on title and key content
            content_hash = hashlib.md5(
                f"{doc.title}_{doc.country}_{doc.regulation_type}".lower().encode()
            ).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_docs.append(doc)
            else:
                logger.debug(f"Removing duplicate document: {doc.title}")
        
        logger.info(f"Deduplicated {len(documents)} documents to {len(unique_docs)} unique documents")
        return unique_docs
    
    def validate_documents(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """Validate document quality and relevance"""
        validated = []
        
        for doc in documents:
            if self._is_valid_document(doc):
                validated.append(doc)
            else:
                logger.debug(f"Filtered out invalid document: {doc.title}")
        
        logger.info(f"Validated {len(validated)}/{len(documents)} documents")
        return validated
    
    def _is_valid_document(self, doc: RegulatoryDocument) -> bool:
        """Check if document meets quality standards"""
        
        # Check required fields
        if not doc.title or len(doc.title.strip()) < 5:
            return False
        
        if not doc.content or len(doc.content.strip()) < 20:
            return False
        
        if not doc.country or len(doc.country.strip()) < 2:
            return False
        
        # Check for reasonable content length
        if len(doc.content) > 100000:  # 100KB limit
            logger.warning(f"Document content too large: {doc.title}")
            return False
        
        # Check relevance score
        if doc.relevance_score < 0.3:
            return False
        
        return True
    
    def rank_documents_by_relevance(
        self, 
        documents: List[RegulatoryDocument], 
        startup_info: Any
    ) -> List[RegulatoryDocument]:
        """Rank documents by relevance to startup"""
        
        if not documents:
            return []
        
        # Enhanced relevance scoring
        for doc in documents:
            score = self._calculate_relevance_score(doc, startup_info)
            doc.relevance_score = score
        
        # Sort by relevance score (descending)
        return sorted(documents, key=lambda x: x.relevance_score, reverse=True)
    
    def _calculate_relevance_score(self, doc: RegulatoryDocument, startup_info: Any) -> float:
        """Calculate detailed relevance score"""
        score = 0.5  # Base score
        
        # Country relevance (most important)
        if doc.country.lower() in [c.lower() for c in startup_info.target_countries]:
            score += 0.3
        
        # Industry relevance
        if startup_info.industry.lower() in doc.content.lower():
            score += 0.25
        elif any(activity.lower() in doc.content.lower() for activity in startup_info.business_activities):
            score += 0.15
        
        # Data handling relevance
        if hasattr(startup_info, 'data_handling') and startup_info.data_handling:
            data_types = [dt.lower() for dt in startup_info.data_handling]
            if any(data_type in doc.content.lower() for data_type in data_types):
                score += 0.2
        
        # Regulation type bonus
        priority_types = ['data_protection', 'financial_regulation', 'licensing']
        if doc.regulation_type in priority_types:
            score += 0.1
        
        # Authority credibility bonus
        if doc.authority and any(term in doc.authority.lower() 
                               for term in ['government', 'commission', 'authority', 'ministry']):
            score += 0.1
        
        # URL availability bonus
        if doc.url and doc.url.startswith('http'):
            score += 0.05
        
        # Ensure score is between 0 and 1
        return min(max(score, 0.0), 1.0)
    
    def filter_documents_by_country(
        self, 
        documents: List[RegulatoryDocument], 
        target_country: str
    ) -> List[RegulatoryDocument]:
        """Filter documents to ensure they belong to the target country"""
        
        filtered = []
        target_lower = target_country.lower().strip()
        
        for doc in documents:
            if self._is_country_specific(doc, target_country):
                filtered.append(doc)
            else:
                logger.debug(f"Filtered out non-{target_country} document: {doc.title}")
        
        return filtered
    
    def _is_country_specific(self, doc: RegulatoryDocument, target_country: str) -> bool:
        """Check if document is specific to the target country"""
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
        
        return False
    
    def extract_top_documents(
        self, 
        documents: List[RegulatoryDocument], 
        limit: int = 20
    ) -> List[RegulatoryDocument]:
        """Extract top N most relevant documents"""
        
        # Sort by relevance if not already sorted
        sorted_docs = sorted(documents, key=lambda x: x.relevance_score, reverse=True)
        
        top_docs = sorted_docs[:limit]
        
        logger.info(f"Selected top {len(top_docs)} documents from {len(documents)} total")
        
        return top_docs

# Global processor instance for import
document_processor = DocumentProcessor() 