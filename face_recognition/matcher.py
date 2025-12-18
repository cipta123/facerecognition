"""
Matcher untuk face recognition dengan cosine similarity
"""
import numpy as np
from typing import List, Dict, Optional
from scipy.spatial.distance import cosine

from face_recognition.config import COSINE_SIMILARITY_THRESHOLD, TOP_K_MATCHES
from face_recognition.database import FaceDatabase


class FaceMatcher:
    """Matcher untuk mencari wajah yang mirip menggunakan cosine similarity."""
    
    def __init__(self, database: FaceDatabase = None):
        """Initialize matcher dengan database."""
        self.db = database or FaceDatabase()
        self.threshold = COSINE_SIMILARITY_THRESHOLD
        self.top_k = TOP_K_MATCHES
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity antara dua embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (0-1, higher = more similar)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity = dot product / (norm1 * norm2)
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))
    
    def match(self, query_embedding: np.ndarray, threshold: float = None, 
              top_k: int = None) -> List[Dict]:
        """
        Match query embedding dengan database.
        
        Args:
            query_embedding: Query embedding vector
            threshold: Minimum similarity threshold (default dari config)
            top_k: Number of top results (default dari config)
            
        Returns:
            List of matches: [{'nim': str, 'confidence': float, 'photo_path': str}, ...]
        """
        if threshold is None:
            threshold = self.threshold
        if top_k is None:
            top_k = self.top_k
        
        # Search in database
        matches = self.db.search_similar(query_embedding, threshold, top_k)
        
        return matches
    
    def match_batch(self, query_embeddings: List[np.ndarray], threshold: float = None) -> List[List[Dict]]:
        """
        Match multiple query embeddings.
        
        Args:
            query_embeddings: List of query embedding vectors
            threshold: Minimum similarity threshold
            
        Returns:
            List of match results for each query
        """
        results = []
        for embedding in query_embeddings:
            matches = self.match(embedding, threshold)
            results.append(matches)
        return results
    
    def get_best_match(self, query_embedding: np.ndarray, threshold: float = None) -> Optional[Dict]:
        """
        Get best match (top 1).
        
        Args:
            query_embedding: Query embedding vector
            threshold: Minimum similarity threshold
            
        Returns:
            Best match dict atau None jika tidak ada match di atas threshold
        """
        matches = self.match(query_embedding, threshold, top_k=1)
        if matches:
            return matches[0]
        return None

