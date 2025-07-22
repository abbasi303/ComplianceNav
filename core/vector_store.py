"""
Vector Store Integration using Chroma for Regulatory Documents
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from loguru import logger
from config.settings import settings
import hashlib
import json



class RegulatoryVectorStore:
    """Vector store for regulatory documents using Chroma"""
    
    def __init__(self):
        """Initialize the vector store"""
        try:
            # Initialize Chroma client with persistence
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Get or create collections
            self.regulations_collection = self._get_or_create_collection(
                "regulations", 
                "Regulatory documents and compliance information"
            )
            
            self.compliance_cases_collection = self._get_or_create_collection(
                "compliance_cases",
                "Historical compliance cases and precedents"
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _get_or_create_collection(self, name: str, description: str):
        """Get or create a Chroma collection"""
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Retrieved existing collection: {name}")
            return collection
        except Exception:
            collection = self.client.create_collection(
                name=name,
                metadata={"description": description}
            )
            logger.info(f"Created new collection: {name}")
            return collection
    
    def add_regulatory_document(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """
        Add a regulatory document to the vector store
        
        Args:
            content: The document content
            metadata: Document metadata (country, regulation_type, source, etc.)
            document_id: Optional document ID, will generate if not provided
            
        Returns:
            Document ID
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                content_hash = hashlib.md5(content.encode()).hexdigest()
                document_id = f"reg_{content_hash[:12]}"
            
            # Prepare metadata
            doc_metadata = {
                "content_length": len(content),
                "document_type": "regulation",
                **metadata
            }
            
            # Add to collection
            self.regulations_collection.add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[document_id]
            )
            
            logger.info(f"Added regulatory document: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding regulatory document: {e}")
            raise
    
    def search_regulations(
        self, 
        query: str, 
        n_results: int = 10,
        country_filter: Optional[str] = None,
        regulation_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant regulations
        
        Args:
            query: Search query
            n_results: Number of results to return
            country_filter: Filter by country
            regulation_type_filter: Filter by regulation type
            
        Returns:
            List of relevant regulations with metadata
        """
        try:
            # Build where clause for filtering
            where_clause = {}
            if country_filter:
                where_clause["country"] = {"$eq": country_filter}
            if regulation_type_filter:
                where_clause["regulation_type"] = {"$eq": regulation_type_filter}
            
            # Search in regulations collection
            results = self.regulations_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.debug(f"Found {len(formatted_results)} regulations for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching regulations: {e}")
            return []
    
    def add_compliance_case(
        self, 
        case_description: str, 
        outcome: str,
        metadata: Dict[str, Any],
        case_id: Optional[str] = None
    ) -> str:
        """
        Add a compliance case to the vector store
        
        Args:
            case_description: Description of the compliance case
            outcome: The outcome/resolution
            metadata: Case metadata (industry, country, regulation_violated, etc.)
            case_id: Optional case ID
            
        Returns:
            Case ID
        """
        try:
            # Generate case ID if not provided
            if not case_id:
                content_hash = hashlib.md5(case_description.encode()).hexdigest()
                case_id = f"case_{content_hash[:12]}"
            
            # Combine description and outcome
            full_content = f"Description: {case_description}\nOutcome: {outcome}"
            
            # Prepare metadata
            case_metadata = {
                "content_length": len(full_content),
                "document_type": "compliance_case",
                "outcome": outcome,
                **metadata
            }
            
            # Add to collection
            self.compliance_cases_collection.add(
                documents=[full_content],
                metadatas=[case_metadata],
                ids=[case_id]
            )
            
            logger.info(f"Added compliance case: {case_id}")
            return case_id
            
        except Exception as e:
            logger.error(f"Error adding compliance case: {e}")
            raise
    
    def search_compliance_cases(
        self, 
        query: str, 
        n_results: int = 5,
        industry_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant compliance cases
        
        Args:
            query: Search query
            n_results: Number of results to return
            industry_filter: Filter by industry
            
        Returns:
            List of relevant compliance cases
        """
        try:
            # Build where clause for filtering
            where_clause = {}
            if industry_filter:
                where_clause["industry"] = {"$eq": industry_filter}
            
            # Search in compliance cases collection
            results = self.compliance_cases_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.debug(f"Found {len(formatted_results)} compliance cases for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching compliance cases: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collections"""
        try:
            regulations_count = self.regulations_collection.count()
            compliance_cases_count = self.compliance_cases_collection.count()
            
            return {
                "regulations_count": regulations_count,
                "compliance_cases_count": compliance_cases_count,
                "total_documents": regulations_count + compliance_cases_count
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

# Global vector store instance
vector_store = RegulatoryVectorStore() 