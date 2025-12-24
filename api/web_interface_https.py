"""
Web Interface dengan HTTPS support
"""
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import ssl
from pathlib import Path
import base64
import numpy as np
from PIL import Image
import io

# Import face recognition components
from face_recognition.encoder import ArcFaceEncoder
from face_recognition.database import FaceDatabase
from face_recognition.matcher import FaceMatcher
from face_recognition.config import FLASK_SECRET_KEY, COSINE_SIMILARITY_THRESHOLD, ENABLE_GAP_VALIDATION
from face_recognition.quality_checker import user_message_for_reason, quality_check_strict
from api.register_helpers import (
    validate_register_request,
    api_response,
    load_image_bgr,
    save_register_photo,
    cleanup_photo
)

# Import HTML template - perlu update dengan logging
# Untuk sekarang, kita akan load template dari file
HTML_TEMPLATE = None

def load_html_template():
    """Load HTML template dari web_interface.py"""
    global HTML_TEMPLATE
    if HTML_TEMPLATE is None:
        import inspect
        from api import web_interface
        # Get HTML_TEMPLATE from web_interface module
        HTML_TEMPLATE = web_interface.HTML_TEMPLATE
    return HTML_TEMPLATE

# Create new Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size
CORS(app)

# Simple rate limiting (in-memory)
from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_store = defaultdict(list)  # {ip: [timestamps]}

def check_rate_limit(ip_address: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
    """
    Check if IP address is within rate limit.
    
    Args:
        ip_address: Client IP address
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    now = datetime.now()
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Clean old entries
    rate_limit_store[ip_address] = [
        ts for ts in rate_limit_store[ip_address] if ts > cutoff
    ]
    
    # Check limit
    if len(rate_limit_store[ip_address]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_store[ip_address].append(now)
    return True

# Initialize components
encoder = None
matcher = None
db = None
face_detector = None  # Cache untuk face detector

def init_components():
    """Initialize encoder, matcher, dan database."""
    global encoder, matcher, db
    if encoder is None:
        print("Initializing face recognition components...")
        encoder = ArcFaceEncoder()
        db = FaceDatabase()
        matcher = FaceMatcher(db)
        print("Components initialized!")

def get_face_detector():
    """Get cached face detector instance."""
    global face_detector
    if face_detector is None:
        from face_recognition.preprocessor import FacePreprocessor
        print("Initializing face detector for detection endpoint...")
        face_detector = FacePreprocessor()
        print("Face detector initialized!")
    return face_detector

@app.route('/')
def index():
    """Serve web interface."""
    template = load_html_template()
    return render_template_string(template)

@app.route('/detect-face', methods=['POST'])
def detect_face():
    """Detect face in image (for visual feedback) - OPTIMIZED for speed."""
    try:
        # Get cached detector (much faster than creating new instance)
        detector = get_face_detector()
        
        # Get image from request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        file = request.files['image']
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Keep original dims for scaling bbox back
        original_width = request.form.get('width', type=int) or image.width
        original_height = request.form.get('height', type=int) or image.height
        
        # OPTIMIZATION: Resize image untuk detection lebih cepat
        # Detection tidak perlu full resolution, cukup max 640px
        max_size = 640
        resized_width, resized_height = image.width, image.height
        if image.width > max_size or image.height > max_size:
            ratio = min(max_size / image.width, max_size / image.height)
            resized_width = int(image.width * ratio)
            resized_height = int(image.height * ratio)
            image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
        
        # Convert to numpy array (BGR for OpenCV)
        image_array = np.array(image.convert('RGB'))
        image_bgr = image_array[:, :, ::-1]  # RGB to BGR
        
        # Use cached detector to detect face
        face_data = detector.detect_face(image_bgr)
        
        if face_data is None:
            return jsonify({
                'success': False,
                'face': None
            })
        
        # Scale bbox back to original size if resized
        bbox = face_data['bbox'].copy()
        if resized_width and resized_height and (resized_width != original_width or resized_height != original_height):
            scale_x = original_width / resized_width
            scale_y = original_height / resized_height
            bbox[0] = int(bbox[0] * scale_x)
            bbox[1] = int(bbox[1] * scale_y)
            bbox[2] = int(bbox[2] * scale_x)
            bbox[3] = int(bbox[3] * scale_y)
        
        # Return bbox in format [x1, y1, x2, y2]
        return jsonify({
            'success': True,
            'face': {
                'bbox': bbox.tolist(),
                'confidence': float(face_data['det_score'])
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/recognize', methods=['POST'])
def recognize():
    """Recognize face dari uploaded image."""
    try:
        init_components()
        
        # Get image from request
        image = None
        
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
        elif request.is_json and 'image' in request.json:
            image_data = request.json['image']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        # Convert to numpy array (BGR for OpenCV)
        image_array = np.array(image.convert('RGB'))
        image_bgr = image_array[:, :, ::-1]  # RGB to BGR
        
        threshold = request.args.get('threshold', type=float) or COSINE_SIMILARITY_THRESHOLD
        
        # Check if this is auto-scan mode
        is_auto_scan = request.headers.get('X-Auto-Scan', 'false').lower() == 'true' or \
                       request.args.get('auto_scan', 'false').lower() == 'true'
        
        # Generate embedding dengan QC RINGAN (real-time)
        embedding, qc = encoder.encode_with_qc(image_bgr, mode="lightweight")

        if embedding is None:
            # QC fail / no face / multiple faces / blur / too small
            reason = (qc or {}).get("reason", "no_face")
            return jsonify({
                'success': False,
                'error': 'Quality check failed',
                'reason': reason,
                'user_message': (qc or {}).get("user_message", user_message_for_reason(reason)),
                'details': (qc or {}).get("details", {})
            }), 200
        
        # Match dengan database
        # Untuk auto-scan, tidak require gap (voting mechanism handle konsistensi)
        require_gap = not is_auto_scan
        matches = matcher.match(embedding, threshold=threshold, require_gap=require_gap)
        
        if not matches:
            return jsonify({
                'success': False,
                'error': 'No match found above threshold',
                'threshold': threshold
            }), 404
        
        best_match = matches[0]
        qc_details = (qc or {}).get("details", {}) if qc else {}

        # Pose ekstrem (real-time) masih boleh, tapi turunkan confidence di response (UX)
        pose_warning = bool(qc_details.get("pose_warning", False))
        confidence_penalty = 0.03 if pose_warning else 0.0
        adjusted_confidence = max(0.0, float(best_match['confidence']) - confidence_penalty)
        
        # Validasi gap (hanya jika diaktifkan di config)
        # Threshold sudah cukup tinggi untuk mengurangi false positive
        # Voting mechanism sudah handle konsistensi untuk auto-scan
        if ENABLE_GAP_VALIDATION and not is_auto_scan and len(matches) > 1:
            best_confidence = best_match['confidence']
            second_confidence = matches[1]['confidence']
            gap = best_confidence - second_confidence
            
            # Untuk manual scan, hanya validasi gap jika confidence rendah (< 0.70)
            if best_confidence < 0.70:
                min_gap_required = 0.08
            elif best_confidence < 0.75:
                min_gap_required = 0.05
            else:
                min_gap_required = 0.02  # Confidence tinggi, gap tidak terlalu penting
            
            if gap < min_gap_required:
                return jsonify({
                    'success': False,
                    'error': 'Match confidence too close to other candidates. Please try again with better lighting/angle.',
                    'best_match': {
                        'nim': best_match['nim'],
                        'confidence': best_confidence
                    },
                    'second_match': {
                        'nim': matches[1]['nim'],
                        'confidence': second_confidence
                    },
                    'gap': gap,
                    'min_required_gap': min_gap_required
                }), 400
        
        # Log recognition
        db.log_recognition(
            nim=best_match['nim'],
            confidence=adjusted_confidence,
            status='success' if best_match['confidence'] >= threshold else 'low_confidence'
        )
        
        return jsonify({
            'success': True,
            'nim': best_match['nim'],
            'confidence': adjusted_confidence,
            'qc': {
                'pose_warning': pose_warning,
                'confidence_penalty': confidence_penalty,
                'details': qc_details
            },
            'matches': matches[:5]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-qc', methods=['POST'])
def check_qc():
    """Check QC untuk frame dari register page tanpa generate embedding."""
    try:
        # Get image from request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'qc_pass': False,
                'reason': 'no_image',
                'user_message': 'Tidak ada gambar yang dikirim'
            }), 400
        
        file = request.files['image']
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to numpy array (BGR for OpenCV)
        image_array = np.array(image.convert('RGB'))
        image_bgr = image_array[:, :, ::-1]  # RGB to BGR
        
        # Get encoder instance
        init_components()
        
        # Detect faces
        faces = encoder.detect_faces(image_bgr)
        
        if len(faces) == 0:
            from face_recognition.quality_checker import QC_SEVERITY, QC_HINTS
            return jsonify({
                'success': True,
                'qc_pass': False,
                'reason': 'no_face',
                'user_message': 'Wajah tidak terdeteksi',
                'severity': QC_SEVERITY.get('no_face', 'error'),
                'hint': QC_HINTS.get('no_face', '')
            })
        
        # Run QC lightweight check
        from face_recognition.quality_checker import quality_check_lightweight, user_message_for_reason
        
        ok, reason, details, selected_face = quality_check_lightweight(image_bgr, faces)
        
        # Extract severity and hint from details
        severity = details.get('severity', 'info')
        hint = details.get('hint', '')
        
        if ok:
            return jsonify({
                'success': True,
                'qc_pass': True,
                'reason': 'ok',
                'user_message': 'Kualitas baik',
                'severity': severity,
                'hint': hint,
                'details': details
            })
        else:
            return jsonify({
                'success': True,
                'qc_pass': False,
                'reason': reason,
                'user_message': user_message_for_reason(reason),
                'severity': severity,
                'hint': hint,
                'details': details
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'qc_pass': False,
            'reason': 'error',
            'user_message': str(e)
        }), 500

@app.route('/api/student/<nim>', methods=['GET'])
def get_student(nim):
    """Get student photo path berdasarkan NIM."""
    try:
        init_components()
        
        # Get photo path from database
        photo_path = db.get_photo_path(nim)
        
        if not photo_path:
            return jsonify({
                'success': False,
                'exists': False,
                'message': f'Mahasiswa dengan NIM {nim} tidak ditemukan'
            }), 404
        
        # Check if file exists
        from pathlib import Path
        from face_recognition.config import PHOTOS_DIR
        
        # photo_path bisa absolute atau relative
        if Path(photo_path).is_absolute():
            photo_file = Path(photo_path)
        else:
            photo_file = PHOTOS_DIR / Path(photo_path).name
        
        if not photo_file.exists():
            return jsonify({
                'success': False,
                'exists': False,
                'message': f'Foto untuk NIM {nim} tidak ditemukan di filesystem'
            }), 404
        
        # Return photo URL (will be served via /api/photo/<nim>)
        return jsonify({
            'success': True,
            'exists': True,
            'nim': nim,
            'photo_path': str(photo_path),
            'photo_url': f'/api/photo/{nim}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/photo/<nim>', methods=['GET'])
def serve_photo(nim):
    """Serve photo file berdasarkan NIM."""
    try:
        init_components()
        
        # Get photo path from database
        photo_path = db.get_photo_path(nim)
        
        if not photo_path:
            return jsonify({
                'success': False,
                'error': 'Photo not found'
            }), 404
        
        from pathlib import Path
        from face_recognition.config import PHOTOS_DIR
        from flask import send_file
        
        # photo_path bisa absolute atau relative
        if Path(photo_path).is_absolute():
            photo_file = Path(photo_path)
        else:
            photo_file = PHOTOS_DIR / Path(photo_path).name
        
        if not photo_file.exists():
            return jsonify({
                'success': False,
                'error': 'Photo file not found'
            }), 404
        
        return send_file(str(photo_file), mimetype='image/jpeg')
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register foto baru ke database dengan QC strict."""
    try:
        # Rate limiting check
        client_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
        if not check_rate_limit(client_ip, max_requests=5, window_seconds=60):
            return api_response(False, "Terlalu banyak request. Silakan coba lagi dalam 1 menit."), 429
        
        init_components()
        
        # Validate request
        try:
            nim, file = validate_register_request(request)
        except ValueError as ve:
            return api_response(False, str(ve)), 400
        
        # Save photo to disk
        photo_path = save_register_photo(nim, file)
        
        # Initialize encoder and load image
        encoder_instance = ArcFaceEncoder()
        image_bgr = encoder_instance.load_image(str(photo_path))
        if image_bgr is None:
            cleanup_photo(photo_path)
            db.log_registration(nim, "failed", "Failed to load image")
            return api_response(False, "Gagal memuat foto"), 400
        
        # Detect faces
        faces = encoder_instance.detect_faces(image_bgr)
        
        if len(faces) == 0:
            cleanup_photo(photo_path)
            db.log_registration(nim, "failed", "No face detected")
            return api_response(False, "Wajah tidak terdeteksi"), 400
        
        # Run QC strict
        ok, reason, details, selected_face = quality_check_strict(image_bgr, faces)
        
        if not ok or selected_face is None:
            cleanup_photo(photo_path)
            msg = user_message_for_reason(reason)
            severity = details.get('severity', 'error')
            hint = details.get('hint', '')
            # Log QC failure
            db.log_registration(nim, "qc_failed", f"{reason}: {msg}")
            return api_response(
                False,
                f"QC gagal: {reason}",
                reason=reason,
                user_message=msg,
                severity=severity,
                hint=hint,
                details=details
            ), 400
        
        # Generate embedding
        embedding = selected_face.normed_embedding
        if embedding is None:
            cleanup_photo(photo_path)
            return api_response(False, "Gagal generate embedding"), 500
        
        # Save to database
        success = db.save_embedding(nim, embedding, str(photo_path))
        
        if success:
            # Log registration success
            db.log_registration(nim, "success", "QC OK & saved")
            return api_response(
                True,
                f"Foto mahasiswa dengan NIM {nim} berhasil diregistrasi",
                nim=nim
            )
        else:
            cleanup_photo(photo_path)
            db.log_registration(nim, "failed", "Database save failed")
            return api_response(False, "Gagal menyimpan ke database"), 500
        
    except ValueError as ve:
        return api_response(False, str(ve)), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return api_response(False, "Internal server error"), 500

@app.route('/api/admin/delete-nim', methods=['POST'])
def delete_nim():
    """Delete NIM from database."""
    try:
        init_components()
        
        # Get NIM from request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.json
        nim = data.get('nim', '').strip()
        
        # Validate NIM format
        if not nim:
            return jsonify({
                'success': False,
                'error': 'NIM tidak boleh kosong'
            }), 400
        
        # Validate NIM format (8-15 digits)
        import re
        if not re.match(r'^\d{8,15}$', nim):
            return jsonify({
                'success': False,
                'error': 'Format NIM tidak valid (harus 8-15 digit)'
            }), 400
        
        # Check if NIM exists
        embedding = db.get_embedding(nim)
        if embedding is None:
            return jsonify({
                'success': False,
                'error': f'NIM {nim} tidak ditemukan di database'
            }), 404
        
        # Delete NIM
        success = db.delete_embedding(nim)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'NIM {nim} berhasil dihapus dari database'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Gagal menghapus NIM dari database'
            }), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Check system status."""
    try:
        init_components()
        stats = db.get_stats()
        return jsonify({
            'success': True,
            'status': 'ready',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Check for SSL certificate
    cert_dir = Path("certs")
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    if cert_path.exists() and key_path.exists():
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cert_path), str(key_path))
        
        print("="*60)
        print("Starting HTTPS server...")
        print(f"Access at: https://localhost:5000")
        print(f"Or: https://10.22.10.131:5000")
        print("="*60)
        print("Note: Browser akan warning tentang self-signed certificate.")
        print("Klik 'Advanced' -> 'Proceed to localhost' untuk continue.")
        print("="*60)
        
        app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=context)
    else:
        print("="*60)
        print("SSL Certificate tidak ditemukan!")
        print("="*60)
        print("Buat certificate dengan:")
        print("  python setup_https.py")
        print("="*60)
        print("\nAtau gunakan web_interface.py biasa (HTTP only)")
        print("dan gunakan opsi Upload Foto jika kamera tidak bisa diakses.")
        print("="*60)

