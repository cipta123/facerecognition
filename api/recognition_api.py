"""
REST API untuk Face Recognition
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
from PIL import Image
import io
from typing import Optional

from face_recognition.encoder import ArcFaceEncoder
from face_recognition.matcher import FaceMatcher
from face_recognition.database import FaceDatabase
from face_recognition.config import FLASK_SECRET_KEY, FLASK_DEBUG, COSINE_SIMILARITY_THRESHOLD, ENABLE_GAP_VALIDATION
from face_recognition.quality_checker import user_message_for_reason

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
CORS(app)  # Enable CORS untuk web interface

# Initialize components
encoder = None
matcher = None
db = None


def init_components():
    """Initialize encoder, matcher, dan database."""
    global encoder, matcher, db
    if encoder is None:
        print("Initializing face recognition components...")
        encoder = ArcFaceEncoder()
        db = FaceDatabase()
        matcher = FaceMatcher(db)
        print("Components initialized!")


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


@app.route('/stats', methods=['GET'])
def stats():
    """Get database statistics."""
    try:
        init_components()
        stats = db.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/recognize', methods=['POST'])
def recognize():
    """
    Recognize face dari uploaded image.
    
    Accepts:
    - Multipart form data dengan 'image' file
    - JSON dengan 'image' base64 encoded string
    
    Returns:
    {
        "success": true,
        "nim": "857264993",
        "confidence": 0.85,
        "matches": [
            {"nim": "857264993", "confidence": 0.85},
            {"nim": "857264994", "confidence": 0.45}
        ]
    }
    """
    try:
        init_components()
        
        # Get image from request
        image = None
        
        # Try multipart form data
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
        # Try JSON with base64
        elif request.is_json and 'image' in request.json:
            image_data = request.json['image']
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            return jsonify({
                'success': False,
                'error': 'No image provided. Send multipart form with "image" file or JSON with "image" base64 string.'
            }), 400
        
        # Convert PIL Image to numpy array (BGR for OpenCV)
        image_array = np.array(image.convert('RGB'))
        image_bgr = image_array[:, :, ::-1]  # RGB to BGR
        
        # Get threshold from request (optional)
        threshold = request.args.get('threshold', type=float)
        if threshold is None:
            threshold = COSINE_SIMILARITY_THRESHOLD
        
        # Generate embedding
        embedding, qc = encoder.encode_with_qc(image_bgr, mode="lightweight")

        if embedding is None:
            reason = (qc or {}).get("reason", "no_face")
            return jsonify({
                'success': False,
                'error': 'Quality check failed',
                'reason': reason,
                'user_message': (qc or {}).get("user_message", user_message_for_reason(reason)),
                'details': (qc or {}).get("details", {})
            }), 200
        
        # Check if this is auto-scan mode (from header or parameter)
        is_auto_scan = request.headers.get('X-Auto-Scan', 'false').lower() == 'true' or \
                       request.args.get('auto_scan', 'false').lower() == 'true'
        
        # Match dengan database (dengan validasi gap)
        # Untuk auto-scan, kita lebih fleksibel dengan gap
        require_gap = not is_auto_scan  # Auto-scan tidak require gap ketat
        matches = matcher.match(embedding, threshold=threshold, require_gap=require_gap)
        
        if not matches:
            print(f"[ERROR] No match found above threshold {threshold}")
            return jsonify({
                'success': False,
                'error': 'No match found above threshold',
                'threshold': threshold
            }), 404
        
        # Get best match
        best_match = matches[0]
        qc_details = (qc or {}).get("details", {}) if qc else {}

        pose_warning = bool(qc_details.get("pose_warning", False))
        confidence_penalty = 0.03 if pose_warning else 0.0
        adjusted_confidence = max(0.0, float(best_match['confidence']) - confidence_penalty)
        
        # Log similarity scores untuk debugging
        if len(matches) > 1:
            print(f"[DEBUG] Best match: NIM {best_match['nim']} (confidence: {best_match['confidence']:.4f})")
            print(f"[DEBUG] Second match: NIM {matches[1]['nim']} (confidence: {matches[1]['confidence']:.4f})")
            print(f"[DEBUG] Gap: {best_match['confidence'] - matches[1]['confidence']:.4f}")
        else:
            print(f"[DEBUG] Single match: NIM {best_match['nim']} (confidence: {best_match['confidence']:.4f})")
        
        # Validasi gap (hanya jika diaktifkan di config)
        # Threshold sudah cukup tinggi untuk mengurangi false positive
        # Voting mechanism sudah handle konsistensi untuk auto-scan
        if ENABLE_GAP_VALIDATION and not is_auto_scan and len(matches) > 1:
            best_confidence = best_match['confidence']
            second_confidence = matches[1]['confidence']
            gap = best_confidence - second_confidence
            
            # Untuk manual scan, hanya validasi gap jika confidence rendah (< 0.70)
            # Jika confidence tinggi, kita lebih percaya pada hasil
            if best_confidence < 0.70:
                # Jika confidence rendah, butuh gap yang lebih besar untuk memastikan akurasi
                min_gap_required = 0.08  # Lebih fleksibel dari default
            elif best_confidence < 0.75:
                min_gap_required = 0.05  # Sedang
            else:
                # Confidence tinggi (> 0.75), gap tidak terlalu penting
                min_gap_required = 0.02  # Sangat fleksibel
            
            if gap < min_gap_required:
                print(f"[WARNING] Gap too small: {gap:.4f} < {min_gap_required:.4f} (best: {best_confidence:.4f}, second: {second_confidence:.4f})")
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
        
        print(f"[SUCCESS] Recognized: NIM {best_match['nim']} with confidence {adjusted_confidence:.4f}")
        
        # Log recognition
        db.log_recognition(
            nim=best_match['nim'],
            confidence=adjusted_confidence,
            status='success' if adjusted_confidence >= threshold else 'low_confidence'
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
            'matches': matches[:5]  # Top 5 matches
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, host='0.0.0.0', port=5000)

