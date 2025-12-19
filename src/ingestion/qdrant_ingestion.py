#!/usr/bin/env python3
"""
Feed unified tenant law knowledge into Qdrant vector database.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import sys

# Add project root to path for config import
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import (
    PROCESSED_DATA_DIR,
    QDRANT_CONFIG,
    PROCESSING_CONFIG
)

# Required packages: pip install qdrant-client sentence-transformers python-dotenv
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from sentence_transformers import SentenceTransformer
    from dotenv import load_dotenv
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Missing dependencies: {e}")
    print("Install with: pip install qdrant-client sentence-transformers python-dotenv")

# Load environment variables
load_dotenv()

class TenantLawQdrant:
    """Handle Qdrant operations for tenant law knowledge base."""
    
    def __init__(self, 
                 collection_name: str = "tenant_law",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 qdrant_url: Optional[str] = None,
                 qdrant_api_key: Optional[str] = None):
        """
        Initialize Qdrant client and embedding model.
        
        Args:
            collection_name: Name of the Qdrant collection
            embedding_model: Name of the sentence transformer model
            qdrant_url: Qdrant server URL (defaults to localhost)
            qdrant_api_key: Qdrant API key (for cloud)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not installed")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize Qdrant client
        if qdrant_url and qdrant_api_key:
            # Cloud setup
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            # Local setup
            self.client = QdrantClient(host="localhost", port=6333)
        
        self.collection_name = collection_name
        
    def create_collection(self, recreate: bool = False):
        """Create or recreate the Qdrant collection."""
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists and recreate:
            print(f"Deleting existing collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            exists = False
        
        if not exists:
            print(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print(f"Collection created with {self.embedding_dim} dimensions")
        else:
            print(f"Collection {self.collection_name} already exists")
    
    def prepare_text_for_embedding(self, chunk: Dict) -> str:
        """Combine relevant text fields for embedding."""
        # Combine the most important fields for semantic search
        text_parts = [
            chunk.get('title', ''),
            chunk.get('key_rule', ''),
            chunk.get('expat_implication', '')
        ]
        return ' '.join(text_parts).strip()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def upload_knowledge_base(self, knowledge_file: str, batch_size: int = 50):
        """Upload the unified tenant law knowledge base to Qdrant."""
        # Load knowledge base
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data['chunks']
        print(f"Loaded {len(chunks)} chunks from {knowledge_file}")
        
        # Prepare points for upload
        points = []
        for i, chunk in enumerate(chunks):
            # Prepare text for embedding
            text = self.prepare_text_for_embedding(chunk)
            
            # Create point with metadata
            point = PointStruct(
                id=chunk.get('id', f"chunk_{i}"),
                vector=None,  # Will be added after embedding
                payload={
                    'title': chunk.get('title', ''),
                    'category': chunk.get('category', ''),
                    'key_rule': chunk.get('key_rule', ''),
                    'expat_implication': chunk.get('expat_implication', ''),
                    'risk_level': chunk.get('risk_level', ''),
                    'source_document': chunk.get('source_document', ''),
                    'text_for_search': text  # Store for reference
                }
            )
            points.append(point)
        
        # Generate embeddings in batches
        all_texts = [p.payload['text_for_search'] for p in points]
        all_embeddings = self.generate_embeddings(all_texts)
        
        # Add embeddings to points
        for point, embedding in zip(points, all_embeddings):
            point.vector = embedding
        
        # Upload in batches
        print(f"Uploading {len(points)} points to Qdrant...")
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            print(f"  Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
        
        print(f"Successfully uploaded {len(points)} points to {self.collection_name}")
        
        # Print collection info
        collection_info = self.client.get_collection(self.collection_name)
        print(f"\nCollection info:")
        print(f"  Points count: {collection_info.points_count}")
        print(f"  Vector size: {collection_info.config.params.vectors.size}")
        print(f"  Distance: {collection_info.config.params.vectors.distance}")
    
    def search(self, 
               query: str, 
               limit: int = 5,
               category_filter: Optional[str] = None,
               risk_filter: Optional[str] = None) -> List[Dict]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results
            category_filter: Filter by category (optional)
            risk_filter: Filter by risk level (optional)
        
        Returns:
            List of matching chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Build filter if specified
        query_filter = None
        if category_filter or risk_filter:
            conditions = []
            if category_filter:
                conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=category_filter))
                )
            if risk_filter:
                conditions.append(
                    FieldCondition(key="risk_level", match=MatchValue(value=risk_filter))
                )
            query_filter = Filter(must=conditions)
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'score': result.score,
                'id': result.id,
                'title': result.payload.get('title', ''),
                'category': result.payload.get('category', ''),
                'key_rule': result.payload.get('key_rule', ''),
                'expat_implication': result.payload.get('expat_implication', ''),
                'risk_level': result.payload.get('risk_level', ''),
                'source_document': result.payload.get('source_document', '')
            })
        
        return formatted_results
    
    def print_search_results(self, results: List[Dict]):
        """Print search results in a readable format."""
        print(f"\nFound {len(results)} results:")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (Score: {result['score']:.3f})")
            print(f"   Category: {result['category']} | Risk: {result['risk_level']}")
            print(f"   Key Rule: {result['key_rule']}")
            print(f"   Expat Implication: {result['expat_implication']}")
            if result['source_document']:
                print(f"   Source: {result['source_document']}")

def main():
    """Main function to run the ingestion process."""
    
    # Configuration
    knowledge_file = PROCESSED_DATA_DIR / "unified_tenant_law_knowledge.json"
    
    # Initialize Qdrant handler
    # For local Qdrant: TenantLawQdrant()
    # For Qdrant Cloud: TenantLawQdrant(
    #     qdrant_url=os.getenv("QDRANT_URL"),
    #     qdrant_api_key=os.getenv("QDRANT_API_KEY")
    # )
    
    try:
        qdrant = TenantLawQdrant()
    except Exception as e:
        print(f"Failed to initialize Qdrant: {e}")
        print("\nTo start Qdrant locally, run:")
        print("docker run -p 6333:6333 qdrant/qdrant")
        return
    
    # Create collection
    qdrant.create_collection(recreate=True)
    
    # Upload knowledge base
    qdrant.upload_knowledge_base(knowledge_file)
    
    # Example searches
    print("\n" + "=" * 80)
    print("EXAMPLE SEARCHES")
    print("=" * 80)
    
    # Search 1: Deposit issues
    results = qdrant.search("How much security deposit can landlord charge?")
    qdrant.print_search_results(results)
    
    # Search 2: Category filtered
    print("\n" + "=" * 80)
    print("SEARCH: termination notice in 'Notice Periods' category")
    print("=" * 80)
    results = qdrant.search(
        "termination notice", 
        category_filter="Notice Periods",
        limit=3
    )
    qdrant.print_search_results(results)
    
    # Search 3: Risk filtered
    print("\n" + "=" * 80)
    print("SEARCH: high risk issues for expats")
    print("=" * 80)
    results = qdrant.search(
        "expat problems",
        risk_filter="red flag",
        limit=3
    )
    qdrant.print_search_results(results)

if __name__ == "__main__":
    main()
