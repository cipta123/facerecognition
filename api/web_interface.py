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
            position: relative;
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
        .btn-switch {
            background: #ed8936;
            color: white;
        }
        .btn-switch:hover {
            background: #dd6b20;
            transform: translateY(-2px);
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
        .btn-auto {
            background: #9f7aea;
            color: white;
        }
        .btn-auto:hover {
            background: #805ad5;
            transform: translateY(-2px);
        }
        .btn-auto.active {
            background: #48bb78;
        }
        .scanning-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(102, 126, 234, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: none;
            animation: pulse 1.5s infinite;
        }
        .scanning-indicator.active {
            display: block;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .status-info {
            text-align: center;
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        
        /* POPUP MODAL STYLES */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }
        .modal-overlay.active {
            display: flex;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            text-align: center;
            position: relative;
            animation: slideUp 0.3s ease;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
        }
        @keyframes slideUp {
            from { 
                transform: translateY(50px);
                opacity: 0;
            }
            to { 
                transform: translateY(0);
                opacity: 1;
            }
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #999;
            transition: color 0.2s;
            background: none;
            border: none;
            padding: 5px 10px;
        }
        .modal-close:hover {
            color: #333;
        }
        .modal-icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        .modal-icon.success {
            color: #48bb78;
        }
        .modal-icon.error {
            color: #f56565;
        }
        .modal-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        .modal-nim {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
            padding: 15px;
            background: #f0f4ff;
            border-radius: 10px;
        }
        .modal-confidence {
            font-size: 18px;
            color: #666;
            margin-bottom: 25px;
        }
        .modal-btn {
            padding: 15px 40px;
            font-size: 18px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .modal-btn.success {
            background: #48bb78;
            color: white;
        }
        .modal-btn.success:hover {
            background: #38a169;
            transform: translateY(-2px);
        }
        .modal-btn.error {
            background: #667eea;
            color: white;
        }
        .modal-btn.error:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .modal-error-msg {
            color: #666;
            font-size: 16px;
            margin-bottom: 20px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Face Recognition - Verifikasi Ujian</h1>
        
        <div class="camera-section">
            <div class="scanning-indicator" id="scanningIndicator">🔍 Scanning...</div>
            <video id="video" autoplay playsinline></video>
            <canvas id="canvas" class="hidden"></canvas>
            
            <div class="controls">
                <button class="btn-auto" onclick="toggleAutoScan()" id="autoScanBtn">▶️ Auto Scan</button>
                <button class="btn-capture" onclick="capturePhoto()">📷 Ambil Foto</button>
                <button class="btn-switch" onclick="switchCamera()" id="switchBtn">🔄 Kamera Belakang</button>
                <label for="fileInput" class="upload-label">📁 Upload Foto</label>
                <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)">
            </div>
            <div class="status-info" id="statusInfo">Siap untuk scanning...</div>
        </div>
        
        <div class="loading" id="loading">
            <p>Memproses foto...</p>
        </div>
    </div>
    
    <!-- POPUP MODAL -->
    <div class="modal-overlay" id="modalOverlay" onclick="closeModalOutside(event)">
        <div class="modal-content" id="modalContent">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <div class="modal-icon" id="modalIcon">✓</div>
            <h2 class="modal-title" id="modalTitle">Identitas Terverifikasi</h2>
            <div class="modal-nim" id="modalNIM">NIM: 857264993</div>
            <div class="modal-confidence" id="modalConfidence">Tingkat Keyakinan: 95.5%</div>
            <button class="modal-btn success" id="modalBtn" onclick="closeModal()">OK - Scan Berikutnya</button>
        </div>
    </div>

    <script>
        let stream = null;
        let currentFacingMode = 'user'; // 'user' = depan, 'environment' = belakang
        let autoScanInterval = null;
        let isAutoScanning = false;
        let isProcessing = false;
        let lastScanTime = 0;
        const SCAN_INTERVAL = 2500; // Scan setiap 2.5 detik
        const MIN_SCAN_INTERVAL = 2000; // Minimum interval 2 detik
        
        // Voting mechanism untuk hasil yang lebih stabil
        let recognitionHistory = [];
        const MAX_HISTORY = 5; // Simpan 5 hasil terakhir
        let stableResult = null; // Hasil yang sudah stabil
        let modalShown = false; // Track apakah modal sedang ditampilkan
        
        // Start camera
        async function startCamera(facingMode = 'user') {
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
                
                // Stop existing stream
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: facingMode,
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    } 
                });
                const video = document.getElementById('video');
                video.srcObject = stream;
                currentFacingMode = facingMode;
                
                // Update button text
                const switchBtn = document.getElementById('switchBtn');
                if (switchBtn) {
                    switchBtn.textContent = facingMode === 'user' ? '🔄 Kamera Belakang' : '🔄 Kamera Depan';
                }
                
                // Wait for video to be ready
                video.onloadedmetadata = () => {
                    console.log('Video ready:', video.videoWidth, 'x', video.videoHeight, 'facingMode:', facingMode);
                    // Start auto scan jika sudah enabled sebelumnya
                    if (isAutoScanning) {
                        startAutoScan();
                    }
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
        
        // Switch camera
        function switchCamera() {
            const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
            console.log('Switching camera from', currentFacingMode, 'to', newFacingMode);
            startCamera(newFacingMode);
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
        
        // Toggle auto scan
        function toggleAutoScan() {
            isAutoScanning = !isAutoScanning;
            const btn = document.getElementById('autoScanBtn');
            const statusInfo = document.getElementById('statusInfo');
            
            if (isAutoScanning) {
                btn.textContent = '⏸️ Stop Auto Scan';
                btn.classList.add('active');
                statusInfo.textContent = 'Auto scan aktif - Scanning setiap ' + (SCAN_INTERVAL/1000) + ' detik...';
                startAutoScan();
            } else {
                btn.textContent = '▶️ Auto Scan';
                btn.classList.remove('active');
                statusInfo.textContent = 'Auto scan dihentikan';
                stopAutoScan();
            }
        }
        
        // Start auto scan
        function startAutoScan() {
            if (autoScanInterval) {
                clearInterval(autoScanInterval);
            }
            
            // Scan pertama langsung
            performAutoScan();
            
            // Set interval untuk scan berikutnya
            autoScanInterval = setInterval(() => {
                performAutoScan();
            }, SCAN_INTERVAL);
        }
        
        // Stop auto scan
        function stopAutoScan() {
            if (autoScanInterval) {
                clearInterval(autoScanInterval);
                autoScanInterval = null;
            }
            const indicator = document.getElementById('scanningIndicator');
            indicator.classList.remove('active');
        }
        
        // Perform auto scan
        function performAutoScan() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            
            // Skip jika masih processing atau video belum ready
            if (isProcessing || !video || !video.videoWidth || !video.videoHeight) {
                return;
            }
            
            // Skip jika interval terlalu cepat
            const now = Date.now();
            if (now - lastScanTime < MIN_SCAN_INTERVAL) {
                return;
            }
            
            try {
                const ctx = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                canvas.toBlob(blob => {
                    if (blob) {
                        sendImage(blob, true); // true = auto scan mode
                    }
                }, 'image/jpeg', 0.9);
                
                lastScanTime = now;
            } catch (err) {
                console.error('Error in auto scan:', err);
            }
        }
        
        // Get most frequent result from history (voting mechanism)
        function getStableResult() {
            if (recognitionHistory.length === 0) {
                return null;
            }
            
            // Count occurrences
            const counts = {};
            recognitionHistory.forEach(result => {
                const key = result.nim;
                if (!counts[key]) {
                    counts[key] = { count: 0, maxConfidence: 0, result: result };
                }
                counts[key].count++;
                if (result.confidence > counts[key].maxConfidence) {
                    counts[key].maxConfidence = result.confidence;
                    counts[key].result = result;
                }
            });
            
            // Find most frequent
            let maxCount = 0;
            let stableResult = null;
            for (const key in counts) {
                if (counts[key].count > maxCount) {
                    maxCount = counts[key].count;
                    stableResult = counts[key].result;
                }
            }
            
            // Only return if appears at least 2 times (40% of history)
            if (maxCount >= 2) {
                return stableResult;
            }
            
            return null;
        }
        
        // Modal functions
        function showModal(isSuccess, nim, confidence, errorMsg = '') {
            const overlay = document.getElementById('modalOverlay');
            const icon = document.getElementById('modalIcon');
            const title = document.getElementById('modalTitle');
            const nimEl = document.getElementById('modalNIM');
            const confEl = document.getElementById('modalConfidence');
            const btn = document.getElementById('modalBtn');
            
            if (isSuccess) {
                icon.textContent = '✓';
                icon.className = 'modal-icon success';
                title.textContent = 'Identitas Terverifikasi';
                nimEl.textContent = `NIM: ${nim}`;
                nimEl.style.display = 'block';
                confEl.textContent = `Tingkat Keyakinan: ${(confidence * 100).toFixed(1)}%`;
                confEl.style.display = 'block';
                btn.textContent = 'OK - Scan Berikutnya';
                btn.className = 'modal-btn success';
            } else {
                icon.textContent = '✗';
                icon.className = 'modal-icon error';
                title.textContent = 'Verifikasi Gagal';
                nimEl.style.display = 'none';
                confEl.textContent = errorMsg || 'Tidak dapat mengenali wajah';
                confEl.className = 'modal-error-msg';
                confEl.style.display = 'block';
                btn.textContent = 'Coba Lagi';
                btn.className = 'modal-btn error';
            }
            
            overlay.classList.add('active');
            modalShown = true;
            
            // Pause auto scan saat modal tampil
            if (isAutoScanning) {
                stopAutoScan();
            }
        }
        
        function closeModal() {
            const overlay = document.getElementById('modalOverlay');
            overlay.classList.remove('active');
            modalShown = false;
            
            // Reset state dan siap untuk scan baru
            recognitionHistory = [];
            stableResult = null;
            
            const statusInfo = document.getElementById('statusInfo');
            statusInfo.textContent = 'Siap untuk scanning...';
            
            // Resume auto scan jika sebelumnya aktif
            if (isAutoScanning) {
                startAutoScan();
            }
        }
        
        function closeModalOutside(event) {
            // Close modal jika klik di luar content
            if (event.target.id === 'modalOverlay') {
                closeModal();
            }
        }
        
        // Keyboard support untuk close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modalShown) {
                closeModal();
            }
            if (e.key === 'Enter' && modalShown) {
                closeModal();
            }
        });
        
        // Send image to API
        async function sendImage(imageBlob, isAutoScan = false) {
            // Skip jika masih processing atau modal sedang tampil
            if (isProcessing || modalShown) {
                return;
            }
            
            isProcessing = true;
            const loading = document.getElementById('loading');
            const scanningIndicator = document.getElementById('scanningIndicator');
            const statusInfo = document.getElementById('statusInfo');
            
            if (isAutoScan) {
                scanningIndicator.classList.add('active');
                statusInfo.textContent = '🔍 Scanning wajah...';
            } else {
                loading.classList.add('active');
                loading.innerHTML = '<p>Memproses foto...</p>';
            }
            
            try {
                const formData = new FormData();
                formData.append('image', imageBlob, 'photo.jpg');
                
                // Add header untuk auto-scan mode
                const headers = {};
                if (isAutoScan) {
                    headers['X-Auto-Scan'] = 'true';
                }
                
                const response = await fetch('/recognize' + (isAutoScan ? '?auto_scan=true' : ''), {
                    method: 'POST',
                    headers: headers,
                    body: formData
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Server error: ${response.status} - ${errorText}`);
                }
                
                const data = await response.json();
                
                if (isAutoScan) {
                    scanningIndicator.classList.remove('active');
                } else {
                    loading.classList.remove('active');
                }
                
                if (data.success) {
                    // Add to history
                    recognitionHistory.push({
                        nim: data.nim,
                        confidence: data.confidence,
                        timestamp: Date.now()
                    });
                    
                    // Keep only last MAX_HISTORY results
                    if (recognitionHistory.length > MAX_HISTORY) {
                        recognitionHistory.shift();
                    }
                    
                    // Get stable result using voting
                    const stable = getStableResult();
                    
                    // Manual scan: langsung tampilkan popup
                    if (!isAutoScan) {
                        showModal(true, data.nim, data.confidence);
                    } 
                    // Auto scan: tunggu hasil stabil
                    else if (stable) {
                        showModal(true, stable.nim, stable.confidence);
                        stableResult = stable;
                    } else {
                        // Still building confidence
                        statusInfo.textContent = `🔍 Mengenali wajah... (${recognitionHistory.length}/${MAX_HISTORY})`;
                    }
                } else {
                    // Error atau tidak ada match
                    if (!isAutoScan) {
                        showModal(false, '', 0, data.error || 'Tidak dapat mengenali wajah');
                    } else {
                        statusInfo.textContent = '❌ ' + (data.error || 'Wajah tidak dikenali');
                    }
                }
            } catch (error) {
                console.error('Error sending image:', error);
                if (isAutoScan) {
                    scanningIndicator.classList.remove('active');
                    statusInfo.textContent = '⚠️ Error: ' + error.message;
                } else {
                    loading.classList.remove('active');
                    showModal(false, '', 0, 'Terjadi kesalahan: ' + error.message);
                }
            } finally {
                isProcessing = false;
            }
        }
        
        // Start camera on load
        window.addEventListener('load', startCamera);
        
        // Stop camera on unload
        window.addEventListener('beforeunload', () => {
            stopAutoScan();
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
        
        // Cleanup on page hide
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && stream) {
                // Optional: stop camera when page is hidden to save resources
                // Uncomment if needed:
                // stream.getTracks().forEach(track => track.stop());
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
    import sys
    # Allow custom port via command line argument
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print("="*60)
    print(f"Starting web interface server on port {port}...")
    print("="*60)
    print(f"Access at:")
    print(f"  - http://localhost:{port}")
    print(f"  - http://127.0.0.1:{port}")
    print(f"  - http://10.22.10.131:{port}")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=port)

