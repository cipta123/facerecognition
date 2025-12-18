"""
Web Interface untuk Face Recognition Ujian
"""
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import os

# Import recognition API functions
from api.recognition_api import app, init_components

# Use the same app from recognition_api to avoid conflicts

# HTML Template untuk web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition - Ujian</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .camera-section {
            margin-bottom: 30px;
        }
        #video {
            width: 100%;
            max-width: 640px;
            border-radius: 10px;
            background: #000;
            display: block;
            margin: 0 auto 20px;
        }
        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .btn-capture {
            background: #667eea;
            color: white;
        }
        .btn-capture:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .btn-upload {
            background: #48bb78;
            color: white;
        }
        .btn-upload:hover {
            background: #38a169;
            transform: translateY(-2px);
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }
        .result.success {
            background: #c6f6d5;
            border: 2px solid #48bb78;
            display: block;
        }
        .result.error {
            background: #fed7d7;
            border: 2px solid #f56565;
            display: block;
        }
        .result h2 {
            margin-bottom: 10px;
        }
        .result .nim {
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
        }
        .result .confidence {
            font-size: 18px;
            color: #4a5568;
            margin-top: 10px;
        }
        .hidden {
            display: none;
        }
        #fileInput {
            display: none;
        }
        .upload-label {
            display: inline-block;
            padding: 12px 24px;
            background: #48bb78;
            color: white;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .upload-label:hover {
            background: #38a169;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Face Recognition - Verifikasi Ujian</h1>
        
        <div class="camera-section">
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas" class="hidden"></canvas>
            
            <div class="controls">
                <button class="btn-capture" onclick="capturePhoto()">📷 Ambil Foto</button>
                <label for="fileInput" class="upload-label">📁 Upload Foto</label>
                <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)">
            </div>
        </div>
        
        <div class="loading" id="loading">
            <p>Memproses foto...</p>
        </div>
        
        <div class="result" id="result">
            <h2 id="resultTitle"></h2>
            <div class="nim" id="resultNIM"></div>
            <div class="confidence" id="resultConfidence"></div>
        </div>
    </div>

    <script>
        let stream = null;
        
        // Start camera
        async function startCamera() {
            try {
                // Check if running on HTTPS or localhost
                const isSecure = window.location.protocol === 'https:' || 
                                window.location.hostname === 'localhost' || 
                                window.location.hostname === '127.0.0.1';
                
                if (!isSecure && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    // Not HTTPS and not localhost - show warning
                    const video = document.getElementById('video');
                    video.style.display = 'none';
                    const warning = document.createElement('div');
                    warning.style.cssText = 'background: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;';
                    warning.innerHTML = `
                        <h3 style="color: #856404; margin-bottom: 10px;">⚠️ Kamera Tidak Dapat Diakses</h3>
                        <p style="color: #856404; margin-bottom: 15px;">
                            Akses kamera memerlukan HTTPS untuk keamanan.<br>
                            Gunakan opsi <strong>Upload Foto</strong> di bawah ini.
                        </p>
                        <p style="color: #856404; font-size: 14px;">
                            Atau akses via: <code>https://${window.location.hostname}:5000</code>
                        </p>
                    `;
                    document.querySelector('.camera-section').insertBefore(warning, document.querySelector('.controls'));
                    return;
                }
                
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'user',
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    } 
                });
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                // Wait for video to be ready
                video.onloadedmetadata = () => {
                    console.log('Video ready:', video.videoWidth, 'x', video.videoHeight);
                };
            } catch (err) {
                console.error('Error accessing camera:', err);
                const video = document.getElementById('video');
                video.style.display = 'none';
                const errorMsg = document.createElement('div');
                errorMsg.style.cssText = 'background: #f8d7da; border: 2px solid #dc3545; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;';
                errorMsg.innerHTML = `
                    <h3 style="color: #721c24; margin-bottom: 10px;">Kamera Tidak Tersedia</h3>
                    <p style="color: #721c24; margin-bottom: 15px;">
                        ${err.name === 'NotAllowedError' ? 'Izin kamera ditolak. Berikan izin di pengaturan browser.' : 
                          err.name === 'NotFoundError' ? 'Tidak ada kamera yang terdeteksi.' : 
                          'Tidak dapat mengakses kamera. Gunakan opsi Upload Foto.'}
                    </p>
                `;
                document.querySelector('.camera-section').insertBefore(errorMsg, document.querySelector('.controls'));
            }
        }
        
        // Capture photo
        function capturePhoto() {
            console.log('Capture photo clicked');
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            
            // Check if video is ready
            if (!video || !video.videoWidth || !video.videoHeight) {
                console.error('Video not ready:', {
                    video: !!video,
                    width: video?.videoWidth,
                    height: video?.videoHeight
                });
                alert('Video belum siap. Tunggu sebentar dan coba lagi.');
                return;
            }
            
            try {
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                console.log('Image captured, converting to blob...');
                canvas.toBlob(blob => {
                    if (blob) {
                        console.log('Blob created, size:', blob.size, 'bytes');
                        sendImage(blob);
                    } else {
                        console.error('Failed to create blob');
                        alert('Gagal mengambil foto. Coba lagi.');
                    }
                }, 'image/jpeg', 0.9);
            } catch (err) {
                console.error('Error capturing photo:', err);
                alert('Error: ' + err.message);
            }
        }
        
        // Handle file upload
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                sendImage(file);
            }
        }
        
        // Send image to API
        async function sendImage(imageBlob) {
            console.log('Sending image to API...');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            loading.classList.add('active');
            loading.innerHTML = '<p>Memproses foto...</p>';
            result.classList.remove('success', 'error');
            result.style.display = 'none';
            
            try {
                const formData = new FormData();
                formData.append('image', imageBlob, 'photo.jpg');
                
                console.log('Sending POST request to /recognize...');
                const response = await fetch('/recognize', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('API Error:', response.status, errorText);
                    throw new Error(`Server error: ${response.status} - ${errorText}`);
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
                loading.classList.remove('active');
                
                if (data.success) {
                    result.classList.add('success');
                    document.getElementById('resultTitle').textContent = '[OK] Identitas Terverifikasi';
                    document.getElementById('resultNIM').textContent = `NIM: ${data.nim}`;
                    document.getElementById('resultConfidence').textContent = 
                        `Tingkat Keyakinan: ${(data.confidence * 100).toFixed(1)}%`;
                    result.style.display = 'block';
                } else {
                    result.classList.add('error');
                    document.getElementById('resultTitle').textContent = '[X] Verifikasi Gagal';
                    document.getElementById('resultNIM').textContent = data.error || 'Tidak dapat mengenali wajah';
                    document.getElementById('resultConfidence').textContent = '';
                    result.style.display = 'block';
                }
            } catch (error) {
                console.error('Error sending image:', error);
                loading.classList.remove('active');
                result.classList.add('error');
                document.getElementById('resultTitle').textContent = '[X] Error';
                document.getElementById('resultNIM').textContent = 'Terjadi kesalahan: ' + error.message;
                document.getElementById('resultConfidence').textContent = 'Cek console untuk detail error';
                result.style.display = 'block';
            }
        }
        
        // Start camera on load
        window.addEventListener('load', startCamera);
        
        // Stop camera on unload
        window.addEventListener('beforeunload', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve web interface."""
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

