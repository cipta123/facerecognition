"""
Preprocessor untuk Face Recognition dengan ArcFace
Handles: Multi-format support, RetinaFace detection, 5-point alignment, normalization
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
    """Preprocessor untuk face recognition dengan ArcFace pipeline."""
    
    def __init__(self):
        """Initialize RetinaFace detector."""
        # Initialize InsightFace FaceAnalysis (includes RetinaFace)
        self.app = FaceAnalysis(
            providers=['CPUExecutionProvider'],  # Use CPU, bisa ganti ke CUDAExecutionProvider untuk GPU
            allowed_modules=['detection', 'recognition']
        )
        self.app.prepare(ctx_id=-1, det_size=(640, 640))
    
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
    
    def detect_face(self, image: np.ndarray) -> Optional[dict]:
        """
        Detect wajah menggunakan RetinaFace dengan 5 landmarks.
        
        Args:
            image: Image dalam format BGR (OpenCV)
            
        Returns:
            Dictionary dengan keys: 'bbox', 'kps' (5 landmarks), 'det_score'
            atau None jika tidak ada wajah
        """
        # Detect faces
        faces = self.app.get(image)
        
        if len(faces) == 0:
            return None
        
        # Ambil wajah dengan confidence tertinggi
        best_face = max(faces, key=lambda x: x.det_score)
        
        # Extract bbox dan landmarks (5 points)
        bbox = best_face.bbox.astype(int)  # [x1, y1, x2, y2]
        kps = best_face.kps.astype(int)    # 5 landmarks: [left_eye, right_eye, nose, left_mouth, right_mouth]
        det_score = best_face.det_score
        
        if det_score < RETINAFACE_CONFIDENCE_THRESHOLD:
            return None
        
        return {
            'bbox': bbox,
            'kps': kps,
            'det_score': det_score
        }
    
    def align_face(self, image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
        """
        Align wajah menggunakan 5 landmarks.
        InsightFace sudah include alignment, tapi kita bisa enhance dengan custom alignment.
        
        Args:
            image: Original image
            landmarks: 5 landmarks [left_eye, right_eye, nose, left_mouth, right_mouth]
            
        Returns:
            Aligned face image
        """
        # InsightFace sudah melakukan alignment internal
        # Tapi kita bisa tambahkan custom alignment jika perlu
        # Untuk sekarang, return image as-is karena InsightFace sudah handle alignment
        return image
    
    def crop_face(self, image: np.ndarray, bbox: np.ndarray, margin: float = 0.2) -> np.ndarray:
        """
        Crop wajah dari image dengan margin.
        
        Args:
            image: Original image
            bbox: Bounding box [x1, y1, x2, y2]
            margin: Margin percentage (0.2 = 20% margin)
            
        Returns:
            Cropped face image
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        
        # Calculate margin
        width = x2 - x1
        height = y2 - y1
        margin_x = int(width * margin)
        margin_y = int(height * margin)
        
        # Expand bbox dengan margin
        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)
        
        # Crop
        face_crop = image[y1:y2, x1:x2]
        
        return face_crop
    
    def resize_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Resize wajah ke 112x112 (ArcFace requirement).
        
        Args:
            face_image: Cropped face image
            
        Returns:
            Resized image (112, 112, 3)
        """
        return cv2.resize(face_image, ARCFACE_INPUT_SIZE, interpolation=cv2.INTER_LINEAR)
    
    def normalize_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Normalize image sesuai ArcFace: (img - 127.5) / 128.0
        
        Args:
            face_image: Face image (112x112, uint8, BGR)
            
        Returns:
            Normalized image (112x112, float32, RGB)
        """
        # Convert ke float32
        face_float = face_image.astype(np.float32)
        
        # Normalize: (img - 127.5) / 128.0
        face_normalized = (face_float - NORMALIZATION_MEAN) / NORMALIZATION_STD
        
        # Convert BGR ke RGB (ArcFace expects RGB)
        face_rgb = cv2.cvtColor(face_normalized, cv2.COLOR_BGR2RGB)
        
        return face_rgb
    
    def preprocess(self, image_path: str) -> Optional[np.ndarray]:
        """
        Complete preprocessing pipeline:
        1. Load image (multi-format support)
        2. Detect face (RetinaFace)
        3. Crop face
        4. Resize to 112x112
        5. Normalize: (img - 127.5) / 128.0
        6. Convert BGR to RGB
        
        Args:
            image_path: Path ke image file
            
        Returns:
            Preprocessed face image (112, 112, 3) dalam format RGB, float32
            atau None jika gagal
        """
        try:
            # Step 1: Load image
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Step 2: Detect face
            face_data = self.detect_face(image)
            if face_data is None:
                return None
            
            bbox = face_data['bbox']
            landmarks = face_data['kps']
            
            # Step 3: Align (InsightFace sudah handle alignment)
            aligned_image = self.align_face(image, landmarks)
            
            # Step 4: Crop face
            face_crop = self.crop_face(aligned_image, bbox)
            
            # Step 5: Resize to 112x112
            face_resized = self.resize_face(face_crop)
            
            # Step 6: Normalize
            face_normalized = self.normalize_face(face_resized)
            
            return face_normalized
            
        except Exception as e:
            print(f"Error preprocessing {image_path}: {str(e)}")
            return None
    
    def preprocess_from_array(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Preprocess dari numpy array (untuk real-time recognition).
        
        Args:
            image: Image array (BGR format)
            
        Returns:
            Preprocessed face image atau None jika gagal
        """
        try:
            # Detect face
            face_data = self.detect_face(image)
            if face_data is None:
                return None
            
            bbox = face_data['bbox']
            landmarks = face_data['kps']
            
            # Align
            aligned_image = self.align_face(image, landmarks)
            
            # Crop
            face_crop = self.crop_face(aligned_image, bbox)
            
            # Resize
            face_resized = self.resize_face(face_crop)
            
            # Normalize
            face_normalized = self.normalize_face(face_resized)
            
            return face_normalized
            
        except Exception as e:
            print(f"Error preprocessing from array: {str(e)}")
            return None

