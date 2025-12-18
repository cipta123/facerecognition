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
from face_recognition.config import FLASK_SECRET_KEY, FLASK_DEBUG, COSINE_SIMILARITY_THRESHOLD

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
        embedding = encoder.encode_from_array(image_bgr)
        
        if embedding is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in image'
            }), 400
        
        # Match dengan database
        matches = matcher.match(embedding, threshold=threshold)
        
        if not matches:
            return jsonify({
                'success': False,
                'error': 'No match found above threshold',
                'threshold': threshold
            }), 404
        
        # Get best match
        best_match = matches[0]
        
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

