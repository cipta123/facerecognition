"""
Configuration settings untuk ArcFace Face Recognition System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
PHOTOS_DIR = BASE_DIR / "output" / "photos"

# ArcFace Model Settings
ARCFACE_MODEL_NAME = "buffalo_l"  # ResNet100 (default) atau "buffalo_s" untuk MobileFaceNet
ARCFACE_INPUT_SIZE = (112, 112)  # Wajib 112x112 untuk ArcFace
ARCFACE_EMBEDDING_SIZE = 512  # 512-D embedding

# Preprocessing Settings
NORMALIZATION_MEAN = 127.5
NORMALIZATION_STD = 128.0
# Formula: (img - 127.5) / 128.0

# RetinaFace Settings
RETINAFACE_CONFIDENCE_THRESHOLD = 0.5
RETINAFACE_NMS_THRESHOLD = 0.4

# Matching Settings
COSINE_SIMILARITY_THRESHOLD = 0.55  # Default threshold (bisa di-tune: 0.5-0.6)
TOP_K_MATCHES = 5  # Return top 5 matches

# Image Format Support
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']

# PostgreSQL Database Settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "face_recognition")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Database Connection String
DB_CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Application Settings
FLASK_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
FLASK_DEBUG = os.getenv("FLASK_ENV", "development") == "development"

# Batch Processing Settings
BATCH_SIZE = 32  # Process 32 images at once
MAX_WORKERS = 4  # Number of parallel workers

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

