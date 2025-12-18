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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Face Recognition - Ujian</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 0;
            margin: 0;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }
        .app-container {
            max-width: 480px;
            margin: 0 auto;
            min-height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            box-shadow: 0 0 50px rgba(0,0,0,0.1);
            position: relative;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 24px;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }
        .header .subtitle {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }
        .camera-section {
            padding: 20px;
            position: relative;
        }
        .video-container {
            position: relative;
            width: 100%;
            border-radius: 20px;
            overflow: hidden;
            background: #000;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        #video {
            width: 100%;
            display: block;
            aspect-ratio: 4/3;
            object-fit: cover;
        }
        .face-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            border-radius: 20px;
        }
        .face-box {
            position: absolute;
            border: 3px solid #48bb78;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(72, 187, 120, 0.5);
            background: rgba(72, 187, 120, 0.1);
            transition: all 0.3s ease;
            animation: facePulse 2s infinite;
        }
        .face-box.detecting {
            border-color: #667eea;
            box-shadow: 0 0 30px rgba(102, 126, 234, 0.7);
            background: rgba(102, 126, 234, 0.15);
            animation: faceDetecting 1s infinite;
        }
        @keyframes facePulse {
            0%, 100% { 
                box-shadow: 0 0 20px rgba(72, 187, 120, 0.5);
            }
            50% { 
                box-shadow: 0 0 30px rgba(72, 187, 120, 0.8);
            }
        }
        @keyframes faceDetecting {
            0%, 100% { 
                box-shadow: 0 0 30px rgba(102, 126, 234, 0.7);
                transform: scale(1);
            }
            50% { 
                box-shadow: 0 0 40px rgba(102, 126, 234, 1);
                transform: scale(1.02);
            }
        }
        .progress-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 0 0 20px 20px;
            overflow: hidden;
            display: none;
        }
        .progress-overlay.active {
            display: block;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.1s linear;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.8);
            position: relative;
            overflow: hidden;
        }
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            animation: progressShine 1.5s infinite;
        }
        @keyframes progressShine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        .face-label {
            position: absolute;
            top: -25px;
            left: 0;
            background: rgba(72, 187, 120, 0.95);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .face-label.detecting {
            background: rgba(102, 126, 234, 0.95);
        }
        .scanning-indicator {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(102, 126, 234, 0.95);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: none;
            animation: pulse 1.5s infinite;
            z-index: 10;
            backdrop-filter: blur(10px);
        }
        .scanning-indicator.active {
            display: block;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(0.98); }
        }
        .status-info {
            text-align: center;
            padding: 12px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #667eea;
            font-weight: 500;
        }
        .controls-frame {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }
        .control-group {
            margin-bottom: 15px;
        }
        .control-group:last-child {
            margin-bottom: 0;
        }
        .control-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-frame {
            position: relative;
            width: 100%;
        }
        .btn-main {
            width: 100%;
            padding: 16px 20px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 600;
            background: white;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
            text-align: left;
            -webkit-tap-highlight-color: transparent;
        }
        .btn-main:active {
            transform: scale(0.98);
        }
        .btn-main .icon {
            font-size: 20px;
            margin-right: 12px;
        }
        .btn-main .text {
            flex: 1;
        }
        .btn-main .arrow {
            font-size: 18px;
            color: #999;
            transition: transform 0.3s;
        }
        .btn-main.active .arrow {
            transform: rotate(180deg);
        }
        .btn-main.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
        }
        .btn-main.primary .arrow {
            color: rgba(255,255,255,0.8);
        }
        .btn-main.success {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border-color: transparent;
        }
        .btn-main.success .arrow {
            color: rgba(255,255,255,0.8);
        }
        .btn-main.warning {
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            color: white;
            border-color: transparent;
        }
        .btn-main.warning .arrow {
            color: rgba(255,255,255,0.8);
        }
        .dropdown-menu {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-top: 8px;
            border-radius: 12px;
            background: #f8f9fa;
        }
        .dropdown-menu.active {
            max-height: 500px;
        }
        .dropdown-item {
            padding: 14px 20px;
            cursor: pointer;
            transition: all 0.2s;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            font-size: 15px;
            color: #333;
        }
        .dropdown-item:last-child {
            border-bottom: none;
        }
        .dropdown-item:active {
            background: #e9ecef;
        }
        .dropdown-item .icon {
            font-size: 18px;
            margin-right: 12px;
            width: 24px;
            text-align: center;
        }
        .hidden {
            display: none;
        }
        #fileInput {
            display: none;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading.active {
            display: block;
        }
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
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
            backdrop-filter: blur(5px);
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
            border-radius: 24px;
            padding: 30px;
            max-width: 90%;
            width: 400px;
            text-align: center;
            position: relative;
            animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
            margin: 20px;
        }
        @keyframes slideUp {
            from { 
                transform: translateY(50px) scale(0.95);
                opacity: 0;
            }
            to { 
                transform: translateY(0) scale(1);
                opacity: 1;
            }
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 28px;
            cursor: pointer;
            color: #999;
            transition: color 0.2s;
            background: none;
            border: none;
            padding: 5px 10px;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }
        .modal-close:active {
            background: #f0f0f0;
            color: #333;
        }
        .modal-icon {
            font-size: 70px;
            margin-bottom: 15px;
            line-height: 1;
        }
        .modal-icon.success {
            color: #48bb78;
        }
        .modal-icon.error {
            color: #f56565;
        }
        .modal-title {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 15px;
            color: #333;
        }
        .modal-nim {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin: 20px 0;
            padding: 15px;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8edff 100%);
            border-radius: 12px;
        }
        .modal-confidence {
            font-size: 16px;
            color: #666;
            margin-bottom: 25px;
            font-weight: 500;
        }
        .modal-btn {
            width: 100%;
            padding: 16px;
            font-size: 16px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .modal-btn:active {
            transform: scale(0.98);
        }
        .modal-btn.success {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        .modal-btn.error {
            background: linear-gradient(135deg, #667eea 0%, #5568d3 100%);
            color: white;
        }
        .modal-error-msg {
            color: #666;
            font-size: 15px;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        @media (max-width: 480px) {
            .app-container {
                max-width: 100%;
            }
            .header h1 {
                font-size: 20px;
            }
            .modal-content {
                padding: 25px;
            }
            .modal-nim {
                font-size: 28px;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1>🔐 Face Recognition</h1>
            <div class="subtitle">Verifikasi Ujian</div>
        </div>
        
        <div class="camera-section">
            <div class="scanning-indicator" id="scanningIndicator">🔍 Scanning...</div>
            <div class="video-container">
                <video id="video" autoplay playsinline></video>
                <canvas class="face-overlay" id="faceOverlay"></canvas>
                <div class="progress-overlay" id="progressOverlay">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
            </div>
            <canvas id="canvas" class="hidden"></canvas>
            
            <div class="status-info" id="statusInfo">Siap untuk scanning...</div>
            
            <div class="controls-frame">
                <div class="control-group">
                    <div class="control-label">Mode Scanning</div>
                    <div class="btn-frame">
                        <button class="btn-main primary" id="scanModeBtn" onclick="toggleDropdown('scanMode')">
                            <span class="icon">📷</span>
                            <span class="text" id="scanModeText">Pilih Mode</span>
                            <span class="arrow">▼</span>
                        </button>
                        <div class="dropdown-menu" id="scanModeMenu">
                            <div class="dropdown-item" onclick="selectScanMode('auto')">
                                <span class="icon">▶️</span>
                                <span>Auto Scan (Otomatis)</span>
                            </div>
                            <div class="dropdown-item" onclick="selectScanMode('manual')">
                                <span class="icon">📸</span>
                                <span>Ambil Foto (Manual)</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="control-group">
                    <div class="control-label">Kamera</div>
                    <div class="btn-frame">
                        <button class="btn-main" id="cameraBtn" onclick="toggleDropdown('camera')">
                            <span class="icon">📹</span>
                            <span class="text" id="cameraText">Kamera Depan</span>
                            <span class="arrow">▼</span>
                        </button>
                        <div class="dropdown-menu" id="cameraMenu">
                            <div class="dropdown-item" onclick="selectCamera('front')">
                                <span class="icon">📱</span>
                                <span>Kamera Depan</span>
                            </div>
                            <div class="dropdown-item" onclick="selectCamera('back')">
                                <span class="icon">📷</span>
                                <span>Kamera Belakang</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="control-group">
                    <div class="control-label">Upload Foto</div>
                    <div class="btn-frame">
                        <button class="btn-main success" onclick="document.getElementById('fileInput').click()">
                            <span class="icon">📁</span>
                            <span class="text">Pilih File dari Galeri</span>
                            <span class="arrow">→</span>
                        </button>
                        <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)" class="hidden">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
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
        let currentScanMode = null; // 'auto' or 'manual'
        
        // Voting mechanism untuk hasil yang lebih stabil
        let recognitionHistory = [];
        const MAX_HISTORY = 5; // Simpan 5 hasil terakhir
        let stableResult = null; // Hasil yang sudah stabil
        let modalShown = false; // Track apakah modal sedang ditampilkan
        let activeDropdown = null; // Track dropdown yang sedang aktif
        let faceDetectionInterval = null; // (legacy) Interval untuk face detection
        let faceDetectionLoop = null; // RequestAnimationFrame loop
        let currentFaceBox = null; // Current detected face box
        let progressAnimation = null; // Progress bar animation
        
        // Face persistence (temporal smoothing) to avoid flicker
        let lastFaceData = null;
        let lastFaceTime = 0;
        const FACE_TIMEOUT = 800; // ms: keep last box for a short time even if a frame misses
        
        // Dropdown functions
        function toggleDropdown(type) {
            const menuId = type === 'scanMode' ? 'scanModeMenu' : 'cameraMenu';
            const btnId = type === 'scanMode' ? 'scanModeBtn' : 'cameraBtn';
            const menu = document.getElementById(menuId);
            const btn = document.getElementById(btnId);
            
            // Close other dropdowns
            if (activeDropdown && activeDropdown !== menu) {
                activeDropdown.classList.remove('active');
                const otherBtn = activeDropdown.previousElementSibling;
                if (otherBtn) otherBtn.classList.remove('active');
            }
            
            // Toggle current dropdown
            if (menu.classList.contains('active')) {
                menu.classList.remove('active');
                btn.classList.remove('active');
                activeDropdown = null;
            } else {
                menu.classList.add('active');
                btn.classList.add('active');
                activeDropdown = menu;
            }
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (activeDropdown && !activeDropdown.contains(e.target) && 
                !activeDropdown.previousElementSibling.contains(e.target)) {
                activeDropdown.classList.remove('active');
                activeDropdown.previousElementSibling.classList.remove('active');
                activeDropdown = null;
            }
        });
        
        // Select scan mode
        function selectScanMode(mode) {
            const btn = document.getElementById('scanModeBtn');
            const text = document.getElementById('scanModeText');
            const menu = document.getElementById('scanModeMenu');
            
            currentScanMode = mode;
            
            if (mode === 'auto') {
                text.textContent = 'Auto Scan (Otomatis)';
                btn.querySelector('.icon').textContent = '▶️';
                if (!isAutoScanning) {
                    toggleAutoScan();
                }
            } else {
                text.textContent = 'Ambil Foto (Manual)';
                btn.querySelector('.icon').textContent = '📸';
                if (isAutoScanning) {
                    toggleAutoScan();
                }
            }
            
            // Close dropdown
            menu.classList.remove('active');
            btn.classList.remove('active');
            activeDropdown = null;
        }
        
        // Select camera
        function selectCamera(camera) {
            const btn = document.getElementById('cameraBtn');
            const text = document.getElementById('cameraText');
            const menu = document.getElementById('cameraMenu');
            const facingMode = camera === 'front' ? 'user' : 'environment';
            
            if (camera === 'front') {
                text.textContent = 'Kamera Depan';
                btn.querySelector('.icon').textContent = '📱';
            } else {
                text.textContent = 'Kamera Belakang';
                btn.querySelector('.icon').textContent = '📷';
            }
            
            // Switch camera
            startCamera(facingMode);
            
            // Close dropdown
            menu.classList.remove('active');
            btn.classList.remove('active');
            activeDropdown = null;
        }
        
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
                
                // Update camera button text
                const cameraText = document.getElementById('cameraText');
                const cameraIcon = document.getElementById('cameraBtn').querySelector('.icon');
                if (facingMode === 'user') {
                    cameraText.textContent = 'Kamera Depan';
                    cameraIcon.textContent = '📱';
                } else {
                    cameraText.textContent = 'Kamera Belakang';
                    cameraIcon.textContent = '📷';
                }
                
                // Wait for video to be ready
                video.onloadedmetadata = () => {
                    console.log('Video ready:', video.videoWidth, 'x', video.videoHeight, 'facingMode:', facingMode);
                    const statusInfo = document.getElementById('statusInfo');
                    statusInfo.textContent = '✅ Kamera siap - Pilih mode scanning';
                    statusInfo.style.background = 'rgba(72, 187, 120, 0.1)';
                    statusInfo.style.color = '#48bb78';
                    
                    // Update overlay size
                    updateOverlaySize();
                    
                    // Start face detection
                    startFaceDetection();
                    
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
        
        // Capture photo (manual mode)
        function capturePhoto() {
            if (isAutoScanning) {
                // If auto scan is active, stop it first
                toggleAutoScan();
            }
            
            console.log('Capture photo clicked');
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            
            // Check if video is ready
            if (!video || !video.videoWidth || !video.videoHeight) {
                console.error('Video not ready');
                const statusInfo = document.getElementById('statusInfo');
                statusInfo.textContent = '⚠️ Video belum siap. Tunggu sebentar...';
                statusInfo.style.background = 'rgba(237, 137, 54, 0.1)';
                statusInfo.style.color = '#ed8936';
                setTimeout(() => {
                    statusInfo.textContent = 'Siap untuk scanning...';
                    statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                    statusInfo.style.color = '#667eea';
                }, 2000);
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
                        sendImage(blob, false); // false = manual mode
                    } else {
                        console.error('Failed to create blob');
                        const statusInfo = document.getElementById('statusInfo');
                        statusInfo.textContent = '❌ Gagal mengambil foto. Coba lagi.';
                        statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                        statusInfo.style.color = '#f56565';
                    }
                }, 'image/jpeg', 0.9);
            } catch (err) {
                console.error('Error capturing photo:', err);
                const statusInfo = document.getElementById('statusInfo');
                statusInfo.textContent = '❌ Error: ' + err.message;
                statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                statusInfo.style.color = '#f56565';
            }
        }
        
        // Handle file upload
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                sendImage(file, false); // false = manual mode
            }
        }
        
        // Toggle auto scan
        function toggleAutoScan() {
            isAutoScanning = !isAutoScanning;
            const statusInfo = document.getElementById('statusInfo');
            const text = document.getElementById('scanModeText');
            
            if (isAutoScanning) {
                text.textContent = 'Auto Scan (Aktif)';
                statusInfo.textContent = '🟢 Auto scan aktif - Scanning setiap ' + (SCAN_INTERVAL/1000) + ' detik...';
                statusInfo.style.background = 'rgba(72, 187, 120, 0.1)';
                statusInfo.style.color = '#48bb78';
                startAutoScan();
            } else {
                text.textContent = 'Auto Scan (Otomatis)';
                statusInfo.textContent = 'Auto scan dihentikan';
                statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                statusInfo.style.color = '#667eea';
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
            // Face detection tetap berjalan untuk visual feedback
        }
        
        // Perform auto scan
        function performAutoScan() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            
            // Skip jika masih processing, modal tampil, atau video belum ready
            if (isProcessing || modalShown || !video || !video.videoWidth || !video.videoHeight) {
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
            if (isAutoScanning) {
                statusInfo.textContent = '🟢 Auto scan aktif - Scanning setiap ' + (SCAN_INTERVAL/1000) + ' detik...';
                statusInfo.style.background = 'rgba(72, 187, 120, 0.1)';
                statusInfo.style.color = '#48bb78';
            } else {
                statusInfo.textContent = 'Siap untuk scanning...';
                statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                statusInfo.style.color = '#667eea';
            }
            
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
            const overlay = document.getElementById('faceOverlay');
            
            // Update face box to detecting state
            if (currentFaceBox) {
                const ctx = overlay.getContext('2d');
                ctx.clearRect(0, 0, overlay.width, overlay.height);
                
                // Draw detecting box
                ctx.strokeStyle = '#667eea';
                ctx.lineWidth = 3;
                ctx.shadowBlur = 30;
                ctx.shadowColor = 'rgba(102, 126, 234, 0.7)';
                ctx.beginPath();
                ctx.roundRect(currentFaceBox.x, currentFaceBox.y, currentFaceBox.width, currentFaceBox.height, 12);
                ctx.stroke();
                
                // Draw detecting label
                ctx.fillStyle = 'rgba(102, 126, 234, 0.95)';
                ctx.shadowBlur = 0;
                const labelText = '🔍 Mencari di Database...';
                ctx.font = '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                const labelWidth = ctx.measureText(labelText).width + 24;
                const labelHeight = 25;
                ctx.beginPath();
                ctx.roundRect(currentFaceBox.x, currentFaceBox.y - labelHeight, labelWidth, labelHeight, 12);
                ctx.fill();
                
                ctx.fillStyle = 'white';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(labelText, currentFaceBox.x + 12, currentFaceBox.y - labelHeight / 2);
            }
            
            // Start progress animation
            startProgressAnimation();
            
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
                
                // Stop progress animation
                stopProgressAnimation();
                
                if (isAutoScan) {
                    scanningIndicator.classList.remove('active');
                } else {
                    loading.classList.remove('active');
                }
                
                // Resume face detection loop if needed
                if (!faceDetectionLoop) {
                    startFaceDetection();
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
                        statusInfo.textContent = '✅ Foto berhasil diproses';
                        statusInfo.style.background = 'rgba(72, 187, 120, 0.1)';
                        statusInfo.style.color = '#48bb78';
                    } 
                    // Auto scan: tunggu hasil stabil
                    else if (stable) {
                        showModal(true, stable.nim, stable.confidence);
                        stableResult = stable;
                    } else {
                        // Still building confidence
                        statusInfo.textContent = `🔍 Mengenali wajah... (${recognitionHistory.length}/${MAX_HISTORY})`;
                        statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                        statusInfo.style.color = '#667eea';
                    }
                } else {
                    // Error atau tidak ada match
                    if (!isAutoScan) {
                        showModal(false, '', 0, data.error || 'Tidak dapat mengenali wajah');
                        statusInfo.textContent = '❌ ' + (data.error || 'Wajah tidak dikenali');
                        statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                        statusInfo.style.color = '#f56565';
                    } else {
                        statusInfo.textContent = '❌ ' + (data.error || 'Wajah tidak dikenali');
                        statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                        statusInfo.style.color = '#f56565';
                    }
                }
            } catch (error) {
                console.error('Error sending image:', error);
                
                // Stop progress animation
                stopProgressAnimation();
                
                // Resume face detection loop if needed
                if (!faceDetectionLoop) {
                    startFaceDetection();
                }
                
                if (isAutoScan) {
                    scanningIndicator.classList.remove('active');
                    statusInfo.textContent = '⚠️ Error: ' + error.message;
                    statusInfo.style.background = 'rgba(237, 137, 54, 0.1)';
                    statusInfo.style.color = '#ed8936';
                } else {
                    loading.classList.remove('active');
                    showModal(false, '', 0, 'Terjadi kesalahan: ' + error.message);
                    statusInfo.textContent = '❌ Error: ' + error.message;
                    statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                    statusInfo.style.color = '#f56565';
                }
            } finally {
                isProcessing = false;
            }
        }
        
        // Face detection functions - OPTIMIZED for speed
        let isDetecting = false; // Prevent concurrent detection requests
        
        async function detectFaceInFrame() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const overlay = document.getElementById('faceOverlay');
            
            // Skip if video not ready, still processing, or already detecting
            if (!video || !video.videoWidth || !video.videoHeight || isDetecting) {
                return;
            }
            
            isDetecting = true;
            
            try {
                // OPTIMIZATION: Resize canvas untuk detection lebih cepat
                // Detection tidak perlu full resolution, cukup 320x240 atau max 640px
                const maxSize = 640;
                let canvasWidth = video.videoWidth;
                let canvasHeight = video.videoHeight;
                let scale = 1;
                
                if (canvasWidth > maxSize || canvasHeight > maxSize) {
                    scale = Math.min(maxSize / canvasWidth, maxSize / canvasHeight);
                    canvasWidth = Math.floor(canvasWidth * scale);
                    canvasHeight = Math.floor(canvasHeight * scale);
                }
                
                // Draw video frame to canvas (resized)
                const ctx = canvas.getContext('2d');
                canvas.width = canvasWidth;
                canvas.height = canvasHeight;
                ctx.drawImage(video, 0, 0, canvasWidth, canvasHeight);
                
                // Convert to blob with lower quality untuk lebih cepat
                canvas.toBlob(async (blob) => {
                    if (!blob) {
                        isDetecting = false;
                        return;
                    }
                    
                    try {
                        const formData = new FormData();
                        formData.append('image', blob, 'frame.jpg');
                        // Send original dimensions untuk scale bbox
                        formData.append('width', video.videoWidth);
                        formData.append('height', video.videoHeight);
                        
                        const response = await fetch('/detect-face', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            if (data.success && data.face) {
                                // Update persistence state
                                lastFaceData = data.face;
                                lastFaceTime = Date.now();
                                drawFaceBox(lastFaceData, video, overlay);
                            } else {
                                // Do NOT clear immediately; keep last box for FACE_TIMEOUT
                                // (render loop will handle clearing after timeout)
                            }
                        } else {
                            // Do NOT clear immediately on a single failed request
                        }
                    } catch (err) {
                        // Silently fail - keep last box (avoid flicker)
                    } finally {
                        isDetecting = false;
                    }
                }, 'image/jpeg', 0.7); // Lower quality (0.7) untuk lebih cepat
            } catch (err) {
                isDetecting = false;
            }
        }
        
        function drawFaceBox(faceData, video, overlay) {
            const ctx = overlay.getContext('2d');
            const videoRect = video.getBoundingClientRect();
            const scaleX = overlay.width / video.videoWidth;
            const scaleY = overlay.height / video.videoHeight;
            
            // Clear previous drawing
            ctx.clearRect(0, 0, overlay.width, overlay.height);
            
            // Calculate box position
            const x = faceData.bbox[0] * scaleX;
            const y = faceData.bbox[1] * scaleY;
            const width = (faceData.bbox[2] - faceData.bbox[0]) * scaleX;
            const height = (faceData.bbox[3] - faceData.bbox[1]) * scaleY;
            
            // Draw face box
            ctx.strokeStyle = '#48bb78';
            ctx.lineWidth = 3;
            ctx.shadowBlur = 20;
            ctx.shadowColor = 'rgba(72, 187, 120, 0.5)';
            ctx.beginPath();
            ctx.roundRect(x, y, width, height, 12);
            ctx.stroke();
            
            // Draw label
            ctx.fillStyle = 'rgba(72, 187, 120, 0.95)';
            ctx.shadowBlur = 0;
            const labelText = 'Wajah Terdeteksi';
            ctx.font = '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            const labelWidth = ctx.measureText(labelText).width + 24;
            const labelHeight = 25;
            ctx.beginPath();
            ctx.roundRect(x, y - labelHeight, labelWidth, labelHeight, 12);
            ctx.fill();
            
            ctx.fillStyle = 'white';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(labelText, x + 12, y - labelHeight / 2);
            
            currentFaceBox = { x, y, width, height };
        }
        
        function clearFaceBox(overlay) {
            const ctx = overlay.getContext('2d');
            ctx.clearRect(0, 0, overlay.width, overlay.height);
            currentFaceBox = null;
        }
        
        function startFaceDetection() {
            // Stop existing detection
            stopFaceDetection();
            
            let lastDetectionTime = 0;
            const DETECTION_INTERVAL = 100; // 100ms = 10 FPS untuk detection (lebih smooth)
            
            // Use requestAnimationFrame untuk lebih smooth
            function detectLoop() {
                const now = Date.now();
                
                // Always render last known face box to avoid flicker (even if no new detection yet)
                const overlay = document.getElementById('faceOverlay');
                const video = document.getElementById('video');
                if (overlay && video && lastFaceData && (now - lastFaceTime) < FACE_TIMEOUT) {
                    drawFaceBox(lastFaceData, video, overlay);
                } else if (overlay && (now - lastFaceTime) >= FACE_TIMEOUT) {
                    // Only clear after timeout (not per-frame)
                    clearFaceBox(overlay);
                    lastFaceData = null;
                }
                
                // Run detection requests periodically; do NOT depend on every frame
                // Keep detection paused while modal shown; during recognition we keep last box rendered.
                if (now - lastDetectionTime >= DETECTION_INTERVAL && !modalShown && !isDetecting && !isProcessing) {
                    lastDetectionTime = now;
                    detectFaceInFrame();
                }
                faceDetectionLoop = requestAnimationFrame(detectLoop);
            }
            
            faceDetectionLoop = requestAnimationFrame(detectLoop);
        }
        
        function stopFaceDetection() {
            if (faceDetectionLoop) {
                cancelAnimationFrame(faceDetectionLoop);
                faceDetectionLoop = null;
            }
            if (faceDetectionInterval) {
                clearInterval(faceDetectionInterval);
                faceDetectionInterval = null;
            }
            isDetecting = false;
            const overlay = document.getElementById('faceOverlay');
            clearFaceBox(overlay);
            lastFaceData = null;
            lastFaceTime = 0;
        }
        
        // Progress bar animation
        function startProgressAnimation() {
            const progressOverlay = document.getElementById('progressOverlay');
            const progressBar = document.getElementById('progressBar');
            
            progressOverlay.classList.add('active');
            progressBar.style.width = '0%';
            
            // Animate from 0% to 100% in 2 seconds
            let progress = 0;
            const duration = 2000; // 2 seconds
            const startTime = Date.now();
            
            if (progressAnimation) {
                cancelAnimationFrame(progressAnimation);
            }
            
            function animate() {
                const elapsed = Date.now() - startTime;
                progress = Math.min((elapsed / duration) * 100, 100);
                progressBar.style.width = progress + '%';
                
                if (progress < 100) {
                    progressAnimation = requestAnimationFrame(animate);
                }
            }
            
            progressAnimation = requestAnimationFrame(animate);
        }
        
        function stopProgressAnimation() {
            if (progressAnimation) {
                cancelAnimationFrame(progressAnimation);
                progressAnimation = null;
            }
            
            const progressOverlay = document.getElementById('progressOverlay');
            const progressBar = document.getElementById('progressBar');
            
            // Complete animation
            progressBar.style.width = '100%';
            
            setTimeout(() => {
                progressOverlay.classList.remove('active');
                progressBar.style.width = '0%';
            }, 300);
        }
        
        // Update overlay canvas size when video size changes
        function updateOverlaySize() {
            const video = document.getElementById('video');
            const overlay = document.getElementById('faceOverlay');
            
            if (video && overlay) {
                const rect = video.getBoundingClientRect();
                overlay.width = rect.width;
                overlay.height = rect.height;
            }
        }
        
        // Polyfill for roundRect if not supported
        if (!CanvasRenderingContext2D.prototype.roundRect) {
            CanvasRenderingContext2D.prototype.roundRect = function(x, y, width, height, radius) {
                this.beginPath();
                this.moveTo(x + radius, y);
                this.lineTo(x + width - radius, y);
                this.quadraticCurveTo(x + width, y, x + width, y + radius);
                this.lineTo(x + width, y + height - radius);
                this.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
                this.lineTo(x + radius, y + height);
                this.quadraticCurveTo(x, y + height, x, y + height - radius);
                this.lineTo(x, y + radius);
                this.quadraticCurveTo(x, y, x + radius, y);
                this.closePath();
            };
        }
        
        // Start camera on load
        window.addEventListener('load', () => {
            startCamera();
            // Update overlay size periodically
            setInterval(updateOverlaySize, 500);
        });
        
        // Stop camera on unload
        window.addEventListener('beforeunload', () => {
            stopAutoScan();
            stopFaceDetection();
            if (progressAnimation) {
                cancelAnimationFrame(progressAnimation);
            }
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

