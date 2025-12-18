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
CORS(app)

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
        
        # Generate embedding
        embedding = encoder.encode_from_array(image_bgr)
        
        if embedding is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in image'
            }), 400
        
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
            confidence=best_match['confidence'],
            status='success' if best_match['confidence'] >= threshold else 'low_confidence'
        )
        
        return jsonify({
            'success': True,
            'nim': best_match['nim'],
            'confidence': best_match['confidence'],
            'matches': matches[:5]
        })
        
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

