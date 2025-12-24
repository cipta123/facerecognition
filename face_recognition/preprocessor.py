"""
Preprocessor untuk Face Recognition dengan ArcFace
VERSI INSIGHTFACE MURNI - Tidak ada alignment manual
InsightFace sudah handle: detection, alignment, crop, resize secara internal
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image
import insightface
from insightface.app import FaceAnalysis

from face_recognition.config import (
    ARCFACE_INPUT_SIZE, NORMALIZATION_MEAN, NORMALIZATION_STD,
    RETINAFACE_CONFIDENCE_THRESHOLD, SUPPORTED_FORMATS
)


class FacePreprocessor:
    """
    Preprocessor untuk face recognition dengan InsightFace pipeline.
    IMPORTANT: Menggunakan InsightFace murni untuk alignment yang konsisten.
    """
    
    def __init__(self):
        """Initialize InsightFace FaceAnalysis."""
        # Initialize InsightFace FaceAnalysis (includes RetinaFace + ArcFace)
        self.app = FaceAnalysis(
            providers=['CPUExecutionProvider'],  # Use CPU, bisa ganti ke CUDAExecutionProvider untuk GPU
            allowed_modules=['detection', 'recognition']
        )
        self.app.prepare(ctx_id=-1, det_size=(640, 640))
        print("FacePreprocessor initialized with InsightFace")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image dengan support multiple formats (JPG, PNG, JPEG).
        Handle PNG dengan alpha channel.
        
        Args:
            image_path: Path ke image file
            
        Returns:
            numpy array (BGR format untuk OpenCV) atau None jika gagal
        """
        image_path = Path(image_path)
        
        # Check format
        if image_path.suffix.lower() not in [f.lower() for f in SUPPORTED_FORMATS]:
            raise ValueError(f"Format tidak didukung: {image_path.suffix}. Hanya support: {SUPPORTED_FORMATS}")
        
        # Try OpenCV first (faster)
        image = cv2.imread(str(image_path))
        
        if image is not None:
            return image
        
        # Fallback ke PIL untuk PNG dengan alpha channel atau format lain
        try:
            pil_image = Image.open(image_path)
            
            # Handle alpha channel (RGBA)
            if pil_image.mode == 'RGBA':
                # Convert RGBA to RGB dengan white background
                rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[3])  # Use alpha channel as mask
                pil_image = rgb_image
            elif pil_image.mode != 'RGB':
                # Convert other modes to RGB
                pil_image = pil_image.convert('RGB')
            
            # Convert PIL to numpy array (RGB)
            image_array = np.array(pil_image)
            # Convert RGB to BGR untuk OpenCV
            image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image
        except Exception as e:
            raise ValueError(f"Gagal load image {image_path}: {str(e)}")
    
    def detect_and_get_face(self, image: np.ndarray) -> Optional[dict]:
        """
        Detect wajah dan dapatkan data face dari InsightFace.
        InsightFace akan handle alignment secara internal.
        
        Args:
            image: Image dalam format BGR (OpenCV)
            
        Returns:
            Dictionary dengan keys: 'face_obj', 'bbox', 'det_score', 'embedding'
            atau None jika tidak ada wajah
        """
        # Detect faces dengan InsightFace
        # InsightFace.get() akan:
        # 1. Detect dengan RetinaFace
        # 2. Align secara internal dengan 5-point landmarks
        # 3. Generate embedding yang sudah aligned
        faces = self.app.get(image)
        
        if len(faces) == 0:
            return None
        
        # Ambil wajah dengan confidence tertinggi
        best_face = max(faces, key=lambda x: x.det_score)
        
        # Check confidence threshold
        if best_face.det_score < RETINAFACE_CONFIDENCE_THRESHOLD:
            return None
        
        return {
            'face_obj': best_face,
            'bbox': best_face.bbox.astype(int),
            'kps': best_face.kps if hasattr(best_face, 'kps') else None,
            'det_score': best_face.det_score,
            'embedding': best_face.normed_embedding  # Sudah aligned & normalized!
        }
    
    def detect_face(self, image: np.ndarray) -> Optional[dict]:
        """
        Detect wajah menggunakan InsightFace.
        Wrapper untuk backward compatibility.
        
        Args:
            image: Image dalam format BGR (OpenCV)
            
        Returns:
            Dictionary dengan keys: 'bbox', 'kps', 'det_score'
            atau None jika tidak ada wajah
        """
        result = self.detect_and_get_face(image)
        if result is None:
            return None
        
        return {
            'bbox': result['bbox'],
            'kps': result['kps'],
            'det_score': result['det_score']
        }

    def detect_all_faces(self, image: np.ndarray, min_score: float = 0.0) -> List[dict]:
        """
        Detect semua wajah (untuk QC / multiple faces check).

        Args:
            image: BGR image
            min_score: filter minimal det_score (default 0.0)

        Returns:
            List of dict: [{'bbox':..., 'kps':..., 'det_score':..., 'face_obj':...}, ...]
        """
        faces = self.app.get(image)
        results: List[dict] = []
        for f in faces:
            score = float(getattr(f, "det_score", 0.0))
            if score < float(min_score):
                continue
            results.append({
                "face_obj": f,
                "bbox": f.bbox.astype(int),
                "kps": f.kps if hasattr(f, "kps") else None,
                "det_score": score,
            })
        return results
    
    def get_embedding_direct(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Dapatkan embedding langsung dari InsightFace.
        INI CARA YANG BENAR - InsightFace handle semua alignment internally.
        
        Args:
            image: Image dalam format BGR (OpenCV)
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        result = self.detect_and_get_face(image)
        if result is None:
            return None
        
        return result['embedding']
    
    def get_embedding_from_path(self, image_path: str) -> Optional[np.ndarray]:
        """
        Dapatkan embedding langsung dari file path.
        Pipeline paling simpel dan konsisten.
        
        Args:
            image_path: Path ke image file
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        try:
            # Load image
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Get embedding langsung dari InsightFace
            return self.get_embedding_direct(image)
            
        except Exception as e:
            print(f"Error getting embedding from {image_path}: {str(e)}")
            return None
    
    # ==================== LEGACY METHODS (untuk backward compatibility) ====================
    # Method-method di bawah ini disimpan untuk backward compatibility
    # tapi TIDAK DIREKOMENDASIKAN untuk digunakan
    
    def preprocess(self, image_path: str) -> Optional[np.ndarray]:
        """
        LEGACY: Complete preprocessing pipeline.
        
        CATATAN: Method ini disimpan untuk backward compatibility.
        Untuk hasil yang KONSISTEN, gunakan get_embedding_from_path() atau get_embedding_direct()
        
        Args:
            image_path: Path ke image file
            
        Returns:
            Preprocessed face image (112, 112, 3) dalam format RGB, float32
            atau None jika gagal
        """
        try:
            # Load image
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Detect face dan dapatkan crop
            face_data = self.detect_and_get_face(image)
            if face_data is None:
                return None
            
            face_obj = face_data['face_obj']
            bbox = face_data['bbox']
            
            # Crop face dengan margin
            face_crop = self._simple_crop(image, bbox, margin=0.3)
            
            # Resize to 112x112
            face_resized = cv2.resize(face_crop, ARCFACE_INPUT_SIZE, interpolation=cv2.INTER_AREA)
            
            # Normalize: (img - 127.5) / 128.0
            face_float = face_resized.astype(np.float32)
            face_normalized = (face_float - NORMALIZATION_MEAN) / NORMALIZATION_STD
            
            # Convert BGR ke RGB
            face_rgb = cv2.cvtColor(face_normalized, cv2.COLOR_BGR2RGB)
            
            return face_rgb
            
        except Exception as e:
            print(f"Error preprocessing {image_path}: {str(e)}")
            return None
    
    def preprocess_from_array(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        LEGACY: Preprocess dari numpy array (untuk real-time recognition).
        
        CATATAN: Method ini disimpan untuk backward compatibility.
        Untuk hasil yang KONSISTEN, gunakan get_embedding_direct()
        
        Args:
            image: Image array (BGR format)
            
        Returns:
            Preprocessed face image atau None jika gagal
        """
        try:
            # Detect face
            face_data = self.detect_and_get_face(image)
            if face_data is None:
                return None
            
            bbox = face_data['bbox']
            
            # Simple crop tanpa alignment manual
            face_crop = self._simple_crop(image, bbox, margin=0.3)
            
            # Resize
            face_resized = cv2.resize(face_crop, ARCFACE_INPUT_SIZE, interpolation=cv2.INTER_AREA)
            
            # Normalize
            face_float = face_resized.astype(np.float32)
            face_normalized = (face_float - NORMALIZATION_MEAN) / NORMALIZATION_STD
            
            # Convert BGR ke RGB
            face_rgb = cv2.cvtColor(face_normalized, cv2.COLOR_BGR2RGB)
            
            return face_rgb
            
        except Exception as e:
            print(f"Error preprocessing from array: {str(e)}")
            return None
    
    def _simple_crop(self, image: np.ndarray, bbox: np.ndarray, margin: float = 0.3) -> np.ndarray:
        """
        Simple crop tanpa alignment.
        
        Args:
            image: Original image
            bbox: Bounding box [x1, y1, x2, y2]
            margin: Margin percentage
            
        Returns:
            Cropped face image
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        
        # Calculate margin
        width = x2 - x1
        height = y2 - y1
        
        # Make it square
        size = max(width, height)
        
        # Calculate center
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # Expand dengan margin
        half_size = int(size * (1 + margin) / 2)
        
        # Calculate new bbox centered
        x1 = max(0, center_x - half_size)
        y1 = max(0, center_y - half_size)
        x2 = min(w, center_x + half_size)
        y2 = min(h, center_y + half_size)
        
        # Crop
        face_crop = image[y1:y2, x1:x2]
        
        # Handle edge case where crop is empty
        if face_crop.size == 0:
            # Fallback: use original bbox
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            face_crop = image[y1:y2, x1:x2]
        
        return face_crop
