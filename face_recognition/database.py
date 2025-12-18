"""
PostgreSQL Database untuk Face Recognition Embeddings
"""
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
import numpy as np
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import pickle

from face_recognition.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_CONNECTION_STRING
)


class FaceDatabase:
    """Database handler untuk face recognition embeddings."""
    
    def __init__(self):
        """Initialize database connection pool."""
        self.connection_pool = None
        self._init_connection_pool()
        self._init_database()
    
    def _init_connection_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,  # min 1, max 20 connections
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            if self.connection_pool:
                print("Database connection pool created successfully")
            else:
                raise Exception("Failed to create connection pool")
        except Exception as e:
            raise RuntimeError(f"Gagal connect ke PostgreSQL: {str(e)}")
    
    def _get_connection(self):
        """Get connection from pool."""
        if self.connection_pool:
            return self.connection_pool.getconn()
        else:
            raise RuntimeError("Connection pool tidak tersedia")
    
    def _return_connection(self, conn):
        """Return connection to pool."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def _init_database(self):
        """Create tables if not exists."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    nim VARCHAR(20) PRIMARY KEY,
                    embedding BYTEA NOT NULL,
                    photo_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create recognition_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recognition_logs (
                    id SERIAL PRIMARY KEY,
                    nim VARCHAR(20),
                    confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    photo_path TEXT,
                    status VARCHAR(20),
                    session_id VARCHAR(50)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nim ON embeddings(nim)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON recognition_logs(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session ON recognition_logs(session_id)
            """)
            
            conn.commit()
            print("Database tables initialized successfully")
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {str(e)}")
            raise
        finally:
            self._return_connection(conn)
    
    def save_embedding(self, nim: str, embedding: np.ndarray, photo_path: str = None) -> bool:
        """
        Save embedding ke database.
        
        Args:
            nim: NIM atau identifier
            embedding: 512-D embedding vector
            photo_path: Path ke foto (optional)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Convert numpy array to bytes
            embedding_bytes = embedding.tobytes()
            
            # Insert or update
            cursor.execute("""
                INSERT INTO embeddings (nim, embedding, photo_path, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (nim) 
                DO UPDATE SET 
                    embedding = EXCLUDED.embedding,
                    photo_path = EXCLUDED.photo_path,
                    updated_at = CURRENT_TIMESTAMP
            """, (nim, embedding_bytes, photo_path))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving embedding for {nim}: {str(e)}")
            return False
        finally:
            self._return_connection(conn)
    
    def get_embedding(self, nim: str) -> Optional[np.ndarray]:
        """
        Get embedding dari database.
        
        Args:
            nim: NIM atau identifier
            
        Returns:
            Embedding vector atau None jika tidak ditemukan
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT embedding FROM embeddings WHERE nim = %s
            """, (nim,))
            
            result = cursor.fetchone()
            if result:
                embedding_bytes = result[0]
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                return embedding
            return None
        except Exception as e:
            print(f"Error getting embedding for {nim}: {str(e)}")
            return None
        finally:
            self._return_connection(conn)
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get semua embeddings dari database.
        
        Returns:
            Dictionary {nim: embedding}
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nim, embedding FROM embeddings
            """)
            
            results = {}
            for row in cursor.fetchall():
                nim = row[0]
                embedding_bytes = row[1]
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                results[nim] = embedding
            
            return results
        except Exception as e:
            print(f"Error getting all embeddings: {str(e)}")
            return {}
        finally:
            self._return_connection(conn)
    
    def search_similar(self, query_embedding: np.ndarray, threshold: float = 0.5, top_k: int = 5) -> List[Dict]:
        """
        Search similar faces menggunakan cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            threshold: Minimum cosine similarity
            top_k: Number of top results
            
        Returns:
            List of {nim, confidence, photo_path} sorted by confidence
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Get all embeddings
            cursor.execute("""
                SELECT nim, embedding, photo_path FROM embeddings
            """)
            
            results = []
            query_norm = np.linalg.norm(query_embedding)
            
            if query_norm == 0:
                return []
            
            for row in cursor.fetchall():
                nim = row[0]
                embedding_bytes = row[1]
                photo_path = row[2]
                
                # Convert bytes to numpy array
                db_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # Calculate cosine similarity
                db_norm = np.linalg.norm(db_embedding)
                if db_norm == 0:
                    continue
                
                cosine_sim = np.dot(query_embedding, db_embedding) / (query_norm * db_norm)
                
                # Clamp to [0, 1] untuk memastikan valid range
                cosine_sim = max(0.0, min(1.0, float(cosine_sim)))
                
                if cosine_sim >= threshold:
                    results.append({
                        'nim': nim,
                        'confidence': cosine_sim,
                        'photo_path': photo_path
                    })
            
            # Sort by confidence (descending)
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Log top results untuk debugging
            if results:
                top_3 = results[:3]
                top_3_str = [(r['nim'], f"{r['confidence']:.4f}") for r in top_3]
                print(f"[DEBUG] Top 3 matches: {top_3_str}")
            
            # Return top_k
            return results[:top_k]
            
        except Exception as e:
            print(f"Error searching similar faces: {str(e)}")
            return []
        finally:
            self._return_connection(conn)
    
    def log_recognition(self, nim: str, confidence: float, photo_path: str = None, 
                      status: str = 'success', session_id: str = None) -> bool:
        """
        Log recognition result.
        
        Args:
            nim: NIM yang di-recognize
            confidence: Confidence score
            photo_path: Path ke foto yang di-recognize
            status: 'success', 'failed', 'low_confidence'
            session_id: Session ID untuk tracking
            
        Returns:
            True jika berhasil
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recognition_logs (nim, confidence, photo_path, status, session_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nim, confidence, photo_path, status, session_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error logging recognition: {str(e)}")
            return False
        finally:
            self._return_connection(conn)
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Count embeddings
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cursor.fetchone()[0]
            
            # Count recognition logs
            cursor.execute("SELECT COUNT(*) FROM recognition_logs")
            total_logs = cursor.fetchone()[0]
            
            # Recent recognitions
            cursor.execute("""
                SELECT COUNT(*) FROM recognition_logs 
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            recent_logs = cursor.fetchone()[0]
            
            return {
                'total_embeddings': total_embeddings,
                'total_logs': total_logs,
                'recent_logs_24h': recent_logs
            }
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {}
        finally:
            self._return_connection(conn)
    
    def close(self):
        """Close connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("Database connection pool closed")

