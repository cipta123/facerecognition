"""
ArcFace Encoder untuk generate 512-D embeddings
"""
import cv2
import numpy as np
from typing import Optional
import insightface

from face_recognition.config import (
    ARCFACE_MODEL_NAME, ARCFACE_EMBEDDING_SIZE, MODELS_DIR
)
from face_recognition.preprocessor import FacePreprocessor


class ArcFaceEncoder:
    """Encoder untuk generate face embeddings menggunakan ArcFace."""
    
    def __init__(self):
        """Initialize ArcFace model dan preprocessor."""
        self.preprocessor = FacePreprocessor()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load ArcFace model dari InsightFace."""
        try:
            # InsightFace akan auto-download model jika belum ada
            # Model akan disimpan di ~/.insightface/models/
            self.model = insightface.app.FaceAnalysis(
                name=ARCFACE_MODEL_NAME,
                providers=['CPUExecutionProvider']  # Bisa ganti ke CUDAExecutionProvider untuk GPU
            )
            self.model.prepare(ctx_id=-1, det_size=(640, 640))
            print(f"ArcFace model '{ARCFACE_MODEL_NAME}' loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Gagal load ArcFace model: {str(e)}")
    
    def encode(self, preprocessed_face: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate embedding dari preprocessed face image.
        
        Args:
            preprocessed_face: Preprocessed face (112x112, RGB, float32, normalized)
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        try:
            # Convert normalized RGB back to uint8 BGR untuk InsightFace API
            # InsightFace expects BGR format, uint8
            face_uint8 = ((preprocessed_face * 128.0) + 127.5).astype(np.uint8)
            face_bgr = cv2.cvtColor(face_uint8, cv2.COLOR_RGB2BGR)
            
            # Use InsightFace to get embedding
            # InsightFace model will detect face and extract embedding
            faces = self.model.get(face_bgr)
            
            if len(faces) == 0:
                # If no face detected, try to use recognition model directly
                # Convert to format expected by recognition model
                face_input = face_bgr.astype(np.float32)
                face_input = (face_input - 127.5) / 128.0
                
                # Get recognition model
                rec_model = self.model.models.get('recognition')
                if rec_model is not None:
                    # Prepare input: CHW format, add batch dimension
                    face_chw = np.transpose(face_input, (2, 0, 1))  # HWC to CHW
                    face_batch = np.expand_dims(face_chw, axis=0)  # Add batch
                    
                    # Get embedding
                    embedding = rec_model.forward(face_batch)
                    embedding = embedding[0]  # Remove batch dimension
                else:
                    return None
            else:
                # Get embedding from detected face
                embedding = faces[0].normed_embedding
            
            if embedding is None:
                return None
            
            # Ensure it's numpy array
            embedding = np.array(embedding)
            
            # Ensure it's 512-D
            if len(embedding) != ARCFACE_EMBEDDING_SIZE:
                # Resize if needed (shouldn't happen with correct model)
                if len(embedding) < ARCFACE_EMBEDDING_SIZE:
                    # Pad with zeros
                    padding = np.zeros(ARCFACE_EMBEDDING_SIZE - len(embedding))
                    embedding = np.concatenate([embedding, padding])
                else:
                    # Truncate
                    embedding = embedding[:ARCFACE_EMBEDDING_SIZE]
            
            # L2 normalize (should already be normalized, but ensure it)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            print(f"Error encoding face: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def encode_from_path(self, image_path: str) -> Optional[np.ndarray]:
        """
        Complete pipeline: Load image → Preprocess → Encode.
        
        Args:
            image_path: Path ke image file
            
        Returns:
            512-D embedding vector atau None jika gagal
        """
        # Preprocess
        preprocessed = self.preprocessor.preprocess(image_path)
        if preprocessed is None:
            return None
        
        # Encode
        embedding = self.encode(preprocessed)
        return embedding
    
    def encode_from_array(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Encode dari numpy array (untuk real-time recognition).
        
        Args:
            image: Image array (BGR format)
            
        Returns:
            512-D embedding vector atau None jika gagal
        """
        # Preprocess
        preprocessed = self.preprocessor.preprocess_from_array(image)
        if preprocessed is None:
            return None
        
        # Encode
        embedding = self.encode(preprocessed)
        return embedding

