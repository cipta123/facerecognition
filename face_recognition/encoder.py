"""
ArcFace Encoder untuk generate 512-D embeddings
VERSI INSIGHTFACE MURNI - Menggunakan embedding langsung dari detection
"""
import cv2
import numpy as np
from typing import Optional, Tuple, Any, List, Dict
import insightface
from insightface.app import FaceAnalysis

from face_recognition.config import (
    ARCFACE_MODEL_NAME, ARCFACE_EMBEDDING_SIZE, MODELS_DIR,
    RETINAFACE_CONFIDENCE_THRESHOLD
)
from face_recognition.quality_checker import (
    quality_check_lightweight,
    quality_check_strict,
    user_message_for_reason,
)


class ArcFaceEncoder:
    """
    Encoder untuk generate face embeddings menggunakan ArcFace.
    VERSI INSIGHTFACE MURNI - embedding langsung dari detection untuk konsistensi maksimal.
    """
    
    def __init__(self):
        """Initialize ArcFace model."""
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load ArcFace model dari InsightFace."""
        try:
            # InsightFace akan auto-download model jika belum ada
            # Model akan disimpan di ~/.insightface/models/
            self.model = FaceAnalysis(
                name=ARCFACE_MODEL_NAME,
                providers=['CPUExecutionProvider']  # Bisa ganti ke CUDAExecutionProvider untuk GPU
            )
            self.model.prepare(ctx_id=-1, det_size=(640, 640))
            print(f"ArcFace model '{ARCFACE_MODEL_NAME}' loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Gagal load ArcFace model: {str(e)}")

    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image as BGR numpy array (OpenCV), with PIL fallback for PNG alpha, etc."""
        try:
            image = cv2.imread(str(image_path))
            if image is not None:
                return image

            # Fallback ke PIL
            from PIL import Image

            pil_image = Image.open(image_path)
            if pil_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[3])
                pil_image = rgb_image
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return image
        except Exception:
            return None

    def detect_faces(self, image_bgr: np.ndarray) -> List[Any]:
        """Return all detected faces from InsightFace."""
        try:
            faces = self.model.get(image_bgr)
            return list(faces) if faces is not None else []
        except Exception:
            return []

    def encode_with_qc(self, image_bgr: np.ndarray, mode: str = "lightweight") -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Encode with Quality Control.
        mode:
          - 'lightweight' for real-time
          - 'strict' for database/registrasi
        Returns: (embedding|None, qc_info|None)
        """
        faces = self.detect_faces(image_bgr)
        if len(faces) == 0:
            qc = {"ok": False, "reason": "no_face", "user_message": user_message_for_reason("no_face"), "details": {"num_faces": 0}}
            return None, qc

        if mode == "strict":
            ok, reason, details, face = quality_check_strict(image_bgr, faces)
        else:
            ok, reason, details, face = quality_check_lightweight(image_bgr, faces)

        if not ok or face is None:
            qc = {"ok": False, "reason": reason, "user_message": user_message_for_reason(reason), "details": details}
            return None, qc

        embedding = getattr(face, "normed_embedding", None)
        if embedding is None:
            qc = {"ok": False, "reason": "no_face", "user_message": user_message_for_reason("no_face"), "details": {"why": "no_embedding"}}
            return None, qc

        embedding = np.array(embedding, dtype=np.float32)
        if len(embedding) != ARCFACE_EMBEDDING_SIZE:
            qc = {"ok": False, "reason": "no_face", "user_message": user_message_for_reason("no_face"), "details": {"why": "bad_embedding_size", "size": len(embedding)}}
            return None, qc

        qc = {"ok": True, "reason": "ok", "user_message": "ok", "details": details}
        return embedding, qc
    
    def encode_from_path(self, image_path: str) -> Optional[np.ndarray]:
        """
        CARA YANG BENAR: Load image → Detection → Embedding langsung.
        InsightFace handle alignment secara internal.
        
        Args:
            image_path: Path ke image file
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        try:
            image = self.load_image(image_path)
            
            if image is None:
                print(f"Failed to load image: {image_path}")
                return None
            
            return self.encode_from_array(image)
            
        except Exception as e:
            print(f"Error encoding from path {image_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def encode_from_array(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        CARA YANG BENAR: Detection → Embedding langsung dari InsightFace.
        InsightFace handle semua alignment secara internal, tidak ada custom preprocessing.
        
        Args:
            image: Image array (BGR format)
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        try:
            # Detect faces dengan InsightFace
            # InsightFace.get() akan:
            # 1. Detect dengan RetinaFace
            # 2. Align secara internal dengan 5-point similarity transform
            # 3. Generate embedding yang sudah aligned & normalized
            faces = self.model.get(image)
            
            if len(faces) == 0:
                return None
            
            # Ambil wajah dengan confidence tertinggi
            best_face = max(faces, key=lambda x: x.det_score)
            
            # Check confidence threshold
            if best_face.det_score < RETINAFACE_CONFIDENCE_THRESHOLD:
                return None
            
            # Ambil embedding langsung dari InsightFace
            # normed_embedding sudah:
            # - Aligned dengan similarity transform (5-point)
            # - Cropped ke 112x112
            # - Normalized
            # - L2 normalized
            embedding = best_face.normed_embedding
            
            if embedding is None:
                return None
            
            # Ensure it's numpy array with correct shape
            embedding = np.array(embedding, dtype=np.float32)
            
            # Verify embedding size
            if len(embedding) != ARCFACE_EMBEDDING_SIZE:
                print(f"Warning: Unexpected embedding size {len(embedding)}, expected {ARCFACE_EMBEDDING_SIZE}")
                return None
            
            return embedding
            
        except Exception as e:
            print(f"Error encoding from array: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    # ==================== LEGACY METHODS (untuk backward compatibility) ====================
    
    def encode(self, preprocessed_face: np.ndarray) -> Optional[np.ndarray]:
        """
        LEGACY: Generate embedding dari preprocessed face image.
        
        CATATAN: Method ini disimpan untuk backward compatibility.
        Untuk hasil yang KONSISTEN, gunakan encode_from_array() atau encode_from_path()
        yang langsung menggunakan InsightFace.
        
        Args:
            preprocessed_face: Preprocessed face (112x112, RGB, float32, normalized)
            
        Returns:
            512-D embedding vector (normalized) atau None jika gagal
        """
        try:
            # Coba gunakan recognition model langsung
            rec_model = self.model.models.get('recognition')
            if rec_model is None:
                # Fallback: convert ke uint8 dan detect ulang
                face_uint8 = ((preprocessed_face * 128.0) + 127.5).astype(np.uint8)
                face_bgr_uint8 = cv2.cvtColor(face_uint8, cv2.COLOR_RGB2BGR)
                faces = self.model.get(face_bgr_uint8)
                if len(faces) > 0:
                    embedding = faces[0].normed_embedding
                else:
                    return None
            else:
                # Convert RGB ke BGR untuk recognition model
                face_bgr = preprocessed_face[:, :, ::-1]  # RGB to BGR
                
                # Prepare input: CHW format, add batch dimension
                face_chw = np.transpose(face_bgr, (2, 0, 1))  # HWC to CHW
                face_batch = np.expand_dims(face_chw, axis=0)  # Add batch dimension
                
                # Get embedding directly from recognition model
                embedding = rec_model.forward(face_batch)
                embedding = embedding[0]  # Remove batch dimension
            
            if embedding is None:
                return None
            
            # Ensure it's numpy array
            embedding = np.array(embedding, dtype=np.float32)
            
            # Ensure it's 512-D
            if len(embedding) != ARCFACE_EMBEDDING_SIZE:
                return None
            
            # L2 normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            else:
                return None
            
            return embedding
            
        except Exception as e:
            print(f"Error encoding face: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
