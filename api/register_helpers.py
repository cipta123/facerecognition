"""
Helper functions untuk endpoint /api/register
"""
from flask import request, jsonify
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import io

from face_recognition.config import PHOTOS_DIR


def validate_register_request(request_obj):
    """
    Validasi request untuk registrasi.
    
    Args:
        request_obj: Flask request object
        
    Returns:
        tuple: (nim, file) jika valid
        
    Raises:
        ValueError: Jika validasi gagal
    """
    # Get NIM
    nim = request_obj.form.get("nim", "").strip()
    if not nim:
        raise ValueError("NIM tidak boleh kosong")
    
    # Validate NIM format (8-15 digits)
    if not nim.isdigit() or len(nim) < 8 or len(nim) > 15:
        raise ValueError("Format NIM tidak valid (harus 8-15 digit)")
    
    # Check image file
    if "image" not in request_obj.files:
        raise ValueError("Foto tidak ditemukan dalam request")
    
    file = request_obj.files["image"]
    if file.filename == "":
        raise ValueError("File foto kosong")
    
    return nim, file


def api_response(success, message="", **data):
    """
    Standard response helper untuk konsistensi.
    
    Args:
        success: Boolean, True jika berhasil
        message: String message
        **data: Additional data untuk response
        
    Returns:
        Flask jsonify response
    """
    response_data = {
        "success": success,
        "message": message
    }
    
    # Add additional data
    if data:
        response_data["data"] = data
    
    return jsonify(response_data)


def load_image_bgr(file):
    """
    Load image dari file upload dan convert ke BGR format.
    
    Args:
        file: Flask FileStorage object
        
    Returns:
        numpy array (BGR format) atau None jika gagal
    """
    try:
        # Read file bytes
        file.seek(0)
        image_bytes = file.read()
        
        # Open with PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Convert RGB to BGR (OpenCV format)
        image_bgr = image_array[:, :, ::-1]
        
        return image_bgr
    except Exception as e:
        print(f"Error loading image: {str(e)}")
        return None


def save_register_photo(nim, file):
    """
    Save foto ke folder photos.
    
    Args:
        nim: NIM mahasiswa
        file: Flask FileStorage object
        
    Returns:
        Path object ke file yang disimpan
    """
    # Determine file extension
    ext = Path(file.filename).suffix.lower() if file.filename else '.jpg'
    if ext not in ['.jpg', '.jpeg', '.png']:
        ext = '.jpg'
    
    # Create filename
    photo_filename = f"{nim}{ext}"
    photo_path = PHOTOS_DIR / photo_filename
    
    # Ensure directory exists
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file.seek(0)
    file.save(str(photo_path))
    
    return photo_path


def cleanup_photo(photo_path):
    """
    Cleanup foto jika terjadi error.
    
    Args:
        photo_path: Path object ke file yang akan dihapus
    """
    try:
        if photo_path and photo_path.exists():
            photo_path.unlink()
    except Exception as e:
        print(f"Error cleaning up photo: {str(e)}")

