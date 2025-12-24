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
        #registerVideo {
            width: 100%;
            display: block;
            aspect-ratio: 4/3; /* Sama dengan home */
            object-fit: cover; /* Sama dengan home */
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
        /* Bottom Navigation Styles */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 480px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 8px 0 calc(8px + env(safe-area-inset-bottom));
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            z-index: 100;
        }
        .nav-item {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px;
            cursor: pointer;
            transition: all 0.3s;
            color: #999;
            -webkit-tap-highlight-color: transparent;
        }
        .nav-item:active {
            transform: scale(0.95);
        }
        .nav-item.active {
            color: #667eea;
        }
        .nav-item .icon {
            font-size: 24px;
            margin-bottom: 4px;
        }
        .nav-item .label {
            font-size: 12px;
            font-weight: 600;
        }
        .page-section {
            display: none;
            padding-bottom: 70px; /* Space untuk bottom nav */
        }
        .page-section.active {
            display: block;
        }
        .app-container {
            padding-bottom: 70px; /* Space untuk bottom nav */
        }
        /* Manual Page Styles */
        .manual-section {
            padding: 20px;
        }
        .search-form {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-label {
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            display: block;
        }
        .form-input {
            width: 100%;
            padding: 14px 16px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            transition: all 0.3s;
            font-family: inherit;
        }
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn-search {
            width: 100%;
            padding: 16px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-search:active {
            transform: scale(0.98);
        }
        .student-photo-container {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            text-align: center;
        }
        .student-photo {
            max-width: 100%;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .student-info {
            margin-top: 15px;
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 12px;
            margin-top: 15px;
            text-align: center;
        }
        /* Register Page Styles */
        .register-section {
            padding: 20px;
        }
        .register-steps {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding: 0 10px;
        }
        .register-step {
            flex: 1;
            text-align: center;
            padding: 12px 16px;
            background: #f7fafc;
            color: #718096;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            position: relative;
            transition: all 0.3s ease;
        }
        .register-step:not(:last-child)::after {
            content: '';
            position: absolute;
            right: -50%;
            top: 50%;
            transform: translateY(-50%);
            width: 100%;
            height: 2px;
            background: #e2e8f0;
            z-index: -1;
        }
        .register-step.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .register-step.completed {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        .register-step.completed::after {
            background: #48bb78;
        }
        .register-form {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }
        .photo-preview-container {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            text-align: center;
        }
        .photo-preview {
            max-width: 100%;
            max-height: 400px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        .btn-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .btn-group button {
            flex: 1;
            padding: 14px;
            font-size: 15px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-group button:active {
            transform: scale(0.98);
        }
        .btn-capture {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        .btn-upload {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-save {
            width: 100%;
            padding: 16px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            color: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-save:active {
            transform: scale(0.98);
        }
        .btn-save:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-delete {
            width: 100%;
            padding: 16px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);
        }
        .btn-delete:hover {
            background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
            box-shadow: 0 6px 20px rgba(245, 101, 101, 0.4);
        }
        .btn-delete:active {
            transform: scale(0.98);
        }
        .btn-delete:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status-message {
            padding: 15px;
            border-radius: 12px;
            margin-top: 15px;
            text-align: center;
            font-weight: 500;
        }
        .status-message.success {
            background: #d4edda;
            color: #155724;
        }
        .status-message.error {
            background: #f8d7da;
            color: #721c24;
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
        <!-- Home Page -->
        <div id="page-home" class="page-section active">
            <div class="header">
                <h1>🔐 Face Recognition</h1>
                <div class="subtitle">Verifikasi Ujian</div>
            </div>
            
            <div class="camera-section">
            <div class="scanning-indicator" id="scanningIndicator">🔍 Scanning...</div>
            <div class="video-container">
                <video id="video" autoplay playsinline muted></video>
                <canvas class="face-overlay" id="faceOverlay"></canvas>
                <div class="progress-overlay" id="progressOverlay">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <!-- Floating button untuk toggle camera di dalam video container -->
                <div style="position: absolute; bottom: 15px; right: 15px; z-index: 10;">
                    <button class="btn-main" id="homeCameraBtn" onclick="toggleHomeCamera()" style="background: rgba(0,0,0,0.6); color: white; border: 2px solid white; padding: 12px; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s;">
                        <span style="font-size: 20px;" id="homeCameraIcon">📱</span>
                    </button>
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
                
            </div>
        </div>
        
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <p>Memproses foto...</p>
            </div>
        </div>
        
        <!-- Manual Page -->
        <div id="page-manual" class="page-section">
            <div class="header">
                <h1>🔍 Cari Mahasiswa</h1>
                <div class="subtitle">Masukkan NIM</div>
            </div>
            
            <div class="manual-section">
                <div class="search-form">
                    <div class="form-group">
                        <label class="form-label" for="nimInput">NIM Mahasiswa</label>
                        <input type="text" id="nimInput" class="form-input" placeholder="Masukkan NIM" />
                    </div>
                    <button class="btn-search" onclick="searchByNIM()">🔍 Cari Mahasiswa</button>
                </div>
                
                <div id="studentResult" style="display: none;">
                    <div class="student-photo-container">
                        <img id="studentPhoto" class="student-photo" src="" alt="Foto Mahasiswa" />
                        <div class="student-info" id="studentInfo"></div>
                    </div>
                </div>
                
                <div id="studentError" class="error-message" style="display: none;"></div>
            </div>
        </div>
        
        <!-- Register Page -->
        <div id="page-register" class="page-section">
            <div class="header">
                <h1>📝 Registrasi Mahasiswa</h1>
                <div class="subtitle">Tambah Foto Baru</div>
            </div>
            
            <div class="register-section">
                <!-- Step Indicator -->
                <div class="register-steps">
                    <span class="register-step active" data-step="1">1. NIM</span>
                    <span class="register-step" data-step="2">2. Capture</span>
                    <span class="register-step" data-step="3">3. Simpan</span>
                </div>
                
                <!-- Video Preview dengan Face Detection -->
                <div class="video-container" id="registerVideoContainer">
                    <video id="registerVideo" autoplay playsinline muted></video>
                    <canvas class="face-overlay" id="registerFaceOverlay"></canvas>
                    <div class="progress-overlay" id="registerProgressOverlay">
                        <div class="progress-bar" id="registerProgressBar"></div>
                    </div>
                    <!-- Floating buttons di dalam video container -->
                    <div style="position: absolute; bottom: 15px; right: 15px; display: flex; gap: 10px; z-index: 10;">
                        <button class="btn-main" id="registerCameraBtn" onclick="toggleRegisterCamera()" style="background: rgba(0,0,0,0.6); color: white; border: 2px solid white; padding: 12px; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s;">
                            <span style="font-size: 20px;" id="registerCameraIcon">📱</span>
                        </button>
                        <button class="btn-main" id="registerManualCaptureBtn" onclick="manualCaptureRegister()" style="background: rgba(72, 187, 120, 0.9); color: white; border: 2px solid white; padding: 12px; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);">
                            <span style="font-size: 20px;">📸</span>
                        </button>
                    </div>
                </div>
                <canvas id="registerCanvas" class="hidden"></canvas>
                
                <!-- Status Indicator -->
                <div class="status-info" id="registerStatusInfo">Mencari wajah...</div>
                
                <!-- Form NIM -->
                <div class="register-form">
                    <div class="form-group">
                        <label class="form-label" for="registerNIMInput">NIM Mahasiswa</label>
                        <input type="text" id="registerNIMInput" class="form-input" placeholder="Masukkan NIM" />
                    </div>
                    
                    <div class="btn-group">
                        <button class="btn-upload" id="btnUploadPhoto" onclick="document.getElementById('registerFileInput').click()" style="display: none;">📁 Upload Foto</button>
                        <button class="btn-main" id="btnToggleUpload" onclick="toggleUploadButton()" style="background: rgba(0, 0, 0, 0.05); color: #666; border: 1px solid rgba(0, 0, 0, 0.1); padding: 8px 16px; border-radius: 8px; font-size: 14px; cursor: pointer; transition: all 0.3s;">
                            <span style="font-size: 18px; vertical-align: middle;">⋯</span> <span style="margin-left: 5px; vertical-align: middle;">Lainnya</span>
                        </button>
                        <input type="file" id="registerFileInput" accept="image/*" onchange="uploadPhotoForRegister(event)" class="hidden">
                    </div>
                </div>
                
                <div id="registerStatus" class="status-message" style="display: none;"></div>
            </div>
        </div>
        
        <!-- Admin Page -->
        <div id="page-admin" class="page-section">
            <div class="header">
                <h1>⚙️ Admin</h1>
                <div class="subtitle">Hapus NIM dari Database</div>
            </div>
            
            <div class="register-section">
                <div class="register-form">
                    <div class="form-group">
                        <label class="form-label" for="adminNIMInput">NIM yang akan dihapus</label>
                        <input type="text" id="adminNIMInput" class="form-input" placeholder="Masukkan NIM" />
                    </div>
                    
                    <button class="btn-delete" id="btnDeleteNIM" onclick="deleteNIM()" style="width: 100%; margin-top: 20px;">
                        🗑️ Hapus NIM dari Database
                    </button>
                </div>
                
                <div id="adminStatus" class="status-message" style="display: none; margin-top: 20px;"></div>
            </div>
        </div>
    </div>
    
    <!-- Register Photo Modal -->
    <div class="modal-overlay" id="registerModalOverlay" onclick="closeRegisterModalOutside(event)">
        <div class="modal-content" id="registerModalContent">
            <button class="modal-close" onclick="closeRegisterModal()">&times;</button>
            <div class="modal-icon success">📸</div>
            <h2 class="modal-title">Foto Berhasil Di-capture</h2>
            <div id="registerModalPreview" style="margin: 20px 0;">
                <img id="registerModalImg" style="max-width: 100%; max-height: 300px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);" src="" alt="Preview Foto" />
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="modal-btn" onclick="retryRegisterCapture()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex: 1;">🔄 Capture Ulang</button>
                <button class="modal-btn success" onclick="saveRegisterPhoto()" style="flex: 1;">💾 Simpan ke Database</button>
            </div>
        </div>
    </div>
    
    <!-- Bottom Navigation -->
    <nav class="bottom-nav">
        <div class="nav-item active" data-page="home" onclick="showPage('home')">
            <div class="icon">🏠</div>
            <div class="label">Home</div>
        </div>
        <div class="nav-item" data-page="manual" onclick="showPage('manual')">
            <div class="icon">🔍</div>
            <div class="label">Manual</div>
        </div>
        <div class="nav-item" data-page="register" onclick="showPage('register')">
            <div class="icon">📝</div>
            <div class="label">Register</div>
        </div>
        <div class="nav-item" data-page="admin" onclick="showPage('admin')">
            <div class="icon">⚙️</div>
            <div class="label">Admin</div>
        </div>
    </nav>
    
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
        
        // Toggle camera untuk home (menggunakan floating button)
        function toggleHomeCamera() {
            const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
            startCamera(newFacingMode);
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
                video.muted = true; // Required for Chrome autoplay
                currentFacingMode = facingMode;
                
                // Update camera button icon (floating button di dalam video container)
                const cameraIcon = document.getElementById('homeCameraIcon');
                if (cameraIcon) {
                    cameraIcon.textContent = facingMode === 'user' ? '📱' : '📷';
                }
                
                // Chrome requires explicit play() call
                try {
                    await video.play();
                } catch (playErr) {
                    console.warn('Video play() failed:', playErr);
                    // Try again after a short delay
                    setTimeout(async () => {
                        try {
                            await video.play();
                        } catch (e) {
                            console.error('Video play() retry failed:', e);
                        }
                    }, 100);
                }
                
                // Wait for video to be ready
                video.onloadedmetadata = async () => {
                    console.log('Video ready:', video.videoWidth, 'x', video.videoHeight, 'facingMode:', facingMode);
                    
                    // Ensure video is playing (Chrome requirement)
                    try {
                        if (video.paused) {
                            await video.play();
                        }
                    } catch (playErr) {
                        console.warn('Video play() in onloadedmetadata failed:', playErr);
                    }
                    
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
                console.error('Error details:', {
                    name: err.name,
                    message: err.message,
                    constraint: err.constraint
                });
                
                const video = document.getElementById('video');
                const statusInfo = document.getElementById('statusInfo');
                
                let errorMessage = 'Tidak dapat mengakses kamera.';
                if (err.name === 'NotAllowedError') {
                    errorMessage = '❌ Izin kamera ditolak. Klik icon 🔒 di address bar dan izinkan akses kamera.';
                } else if (err.name === 'NotFoundError') {
                    errorMessage = '❌ Tidak ada kamera yang terdeteksi.';
                } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                    errorMessage = '❌ Kamera sedang digunakan aplikasi lain. Tutup aplikasi lain yang menggunakan kamera.';
                } else if (err.name === 'OverconstrainedError') {
                    errorMessage = '❌ Kamera tidak mendukung mode yang diminta.';
                } else {
                    errorMessage = `❌ Error: ${err.message || err.name}`;
                }
                
                if (statusInfo) {
                    statusInfo.textContent = errorMessage;
                    statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                    statusInfo.style.color = '#f56565';
                }
                
                // Show error in console for debugging
                console.error('Camera access failed:', errorMessage);
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
            
            // Keyboard support untuk register modal
            const registerModal = document.getElementById('registerModalOverlay');
            if (registerModal && registerModal.classList.contains('active')) {
                if (e.key === 'Escape') {
                    closeRegisterModal();
                }
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
                    const msg = data.user_message || data.error || 'Tidak dapat mengenali wajah';
                    if (!isAutoScan) {
                        showModal(false, '', 0, msg);
                        statusInfo.textContent = '❌ ' + msg;
                        statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                        statusInfo.style.color = '#f56565';
                    } else {
                        statusInfo.textContent = '❌ ' + msg;
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
        
        // ==================== ROUTING SYSTEM ====================
        let currentPage = 'home';
        
        function showPage(page) {
            // Hide all pages
            document.querySelectorAll('.page-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show selected page
            const targetSection = document.getElementById(`page-${page}`);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            // Update nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            const navItem = document.querySelector(`[data-page="${page}"]`);
            if (navItem) {
                navItem.classList.add('active');
            }
            
            currentPage = page;
            
            // Stop auto scan jika pindah dari home page
            if (page !== 'home' && isAutoScanning) {
                toggleAutoScan();
            }
            
            
            // Stop register camera stream jika pindah dari register page
            if (page !== 'register') {
                const registerVideo = document.getElementById('registerVideo');
                if (registerVideo && registerVideo.srcObject) {
                    // Stop tracks dari register video stream
                    const registerStream = registerVideo.srcObject;
                    if (registerStream && registerStream.getTracks) {
                        registerStream.getTracks().forEach(track => track.stop());
                    }
                    registerVideo.srcObject = null;
                }
                // Clear global stream variable jika itu stream dari register
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                }
            }
            
            // Start camera jika pindah ke home atau register page
            if (page === 'home' || page === 'register') {
                // Use same video element for both pages, or create separate for register
                if (page === 'register') {
                    startRegisterCamera();
                } else {
                    // Always start camera for home page (stream sudah di-clear di atas)
                    startCamera();
                }
            }
        }
        
        // Start camera untuk Register page - menggunakan kode yang sama dengan home
        async function startRegisterCamera(facingMode = 'user') {
            // Gunakan startCamera() yang sama, lalu assign ke registerVideo
            try {
                // Check if running on HTTPS or localhost
                const isSecure = window.location.protocol === 'https:' || 
                                window.location.hostname === 'localhost' || 
                                window.location.hostname === '127.0.0.1';
                
                if (!isSecure && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    updateRegisterStatus('⚠️ Kamera memerlukan HTTPS');
                    return;
                }
                
                // Get register video element
                const registerVideo = document.getElementById('registerVideo');
                if (!registerVideo) {
                    updateRegisterStatus('❌ Video element tidak ditemukan');
                    return;
                }
                
                // Stop existing stream if any
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                
                // Stop face detection sementara saat switch camera
                stopRegisterFaceDetection();
                
                // Gunakan stream yang sama dengan home (tidak perlu portrait khusus)
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: facingMode,
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    } 
                });
                
                registerVideo.srcObject = stream;
                registerVideo.muted = true; // Required for Chrome autoplay
                currentFacingMode = facingMode;
                
                // Update camera button icon
                const cameraIcon = document.getElementById('registerCameraIcon');
                if (cameraIcon) {
                    cameraIcon.textContent = facingMode === 'user' ? '📱' : '📷';
                }
                
                // Chrome requires explicit play() call
                try {
                    await registerVideo.play();
                } catch (playErr) {
                    console.warn('Register video play() failed:', playErr);
                    // Try again after a short delay
                    setTimeout(async () => {
                        try {
                            await registerVideo.play();
                        } catch (e) {
                            console.error('Register video play() retry failed:', e);
                        }
                    }, 100);
                }
                
                // Wait for video to be ready
                registerVideo.onloadedmetadata = async () => {
                    console.log('Register video ready:', registerVideo.videoWidth, 'x', registerVideo.videoHeight);
                    
                    // Ensure video is playing (Chrome requirement)
                    try {
                        if (registerVideo.paused) {
                            await registerVideo.play();
                        }
                    } catch (playErr) {
                        console.warn('Register video play() in onloadedmetadata failed:', playErr);
                    }
                    
                    updateRegisterStatus('✅ Kamera siap');
                    
                    // Update overlay size
                    updateRegisterOverlaySize();
                    
                    // Start face detection otomatis (sama seperti home)
                    startRegisterFaceDetection();
                    
                    // Start periodic overlay size updates
                    if (window.registerOverlayUpdateInterval) {
                        clearInterval(window.registerOverlayUpdateInterval);
                    }
                    window.registerOverlayUpdateInterval = setInterval(updateRegisterOverlaySize, 500);
                };
                
                // Also update on resize
                registerVideo.addEventListener('resize', () => {
                    updateRegisterOverlaySize();
                });
            } catch (err) {
                console.error('Error accessing camera for register:', err);
                console.error('Error details:', {
                    name: err.name,
                    message: err.message,
                    constraint: err.constraint
                });
                
                let errorMessage = 'Tidak dapat mengakses kamera.';
                if (err.name === 'NotAllowedError') {
                    errorMessage = '❌ Izin kamera ditolak. Klik icon 🔒 di address bar dan izinkan akses kamera.';
                } else if (err.name === 'NotFoundError') {
                    errorMessage = '❌ Tidak ada kamera yang terdeteksi.';
                } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                    errorMessage = '❌ Kamera sedang digunakan aplikasi lain. Tutup aplikasi lain yang menggunakan kamera.';
                } else if (err.name === 'OverconstrainedError') {
                    errorMessage = '❌ Kamera tidak mendukung mode yang diminta.';
                } else {
                    errorMessage = `❌ Error: ${err.message || err.name}`;
                }
                
                updateRegisterStatus(errorMessage);
            }
        }
        
        // Toggle camera untuk register
        function toggleRegisterCamera() {
            const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
            startRegisterCamera(newFacingMode);
        }
        
        // Toggle visibility tombol upload foto
        function toggleUploadButton() {
            const btnUpload = document.getElementById('btnUploadPhoto');
            const btnToggle = document.getElementById('btnToggleUpload');
            
            if (btnUpload && btnToggle) {
                const isHidden = btnUpload.style.display === 'none' || btnUpload.style.display === '';
                
                if (isHidden) {
                    // Tampilkan tombol upload
                    btnUpload.style.display = 'inline-block';
                    btnToggle.innerHTML = '<span style="font-size: 18px; vertical-align: middle;">▲</span> <span style="margin-left: 5px; vertical-align: middle;">Sembunyikan</span>';
                    btnToggle.style.background = 'rgba(0, 0, 0, 0.05)';
                } else {
                    // Sembunyikan tombol upload
                    btnUpload.style.display = 'none';
                    btnToggle.innerHTML = '<span style="font-size: 18px; vertical-align: middle;">⋯</span> <span style="margin-left: 5px; vertical-align: middle;">Lainnya</span>';
                    btnToggle.style.background = 'rgba(0, 0, 0, 0.05)';
                }
            }
        }
        
        // Manual capture untuk register
        async function manualCaptureRegister() {
            const registerVideo = document.getElementById('registerVideo');
            const registerCanvas = document.getElementById('registerCanvas');
            
            if (!registerVideo || !registerVideo.videoWidth || !registerVideo.videoHeight) {
                updateRegisterStatus('❌ Video belum siap');
                return;
            }
            
            // Validate NIM first
            if (!validateNIM()) {
                return;
            }
            
            try {
                // Capture frame
                const ctx = registerCanvas.getContext('2d');
                registerCanvas.width = registerVideo.videoWidth;
                registerCanvas.height = registerVideo.videoHeight;
                ctx.drawImage(registerVideo, 0, 0);
                
                // Convert to blob
                registerCanvas.toBlob((blob) => {
                    if (blob) {
                        registerPhotoBlob = blob;
                        registerPhotoFile = null;
                        registerPhotoCaptured = true;
                        registerBestFrameBlob = null;
                        registerReadyHistory = [];
                        
                        setRegisterState(RegisterState.CAPTURED);
                        showRegisterModal(blob);
                        updateRegisterStatus('✅ Foto siap - Klik Simpan ke Database');
                    }
                }, 'image/jpeg', 0.95);
            } catch (err) {
                console.error('Error capturing photo:', err);
                updateRegisterStatus('❌ Gagal mengambil foto: ' + err.message);
            }
        }
        
        function updateRegisterOverlaySize() {
            const registerVideo = document.getElementById('registerVideo');
            const overlay = document.getElementById('registerFaceOverlay');
            
            if (registerVideo && overlay) {
                // Get actual displayed video size (bukan container size)
                // Karena object-fit: contain, video mungkin lebih kecil dari container
                const videoRect = registerVideo.getBoundingClientRect();
                const videoAspect = registerVideo.videoWidth / registerVideo.videoHeight;
                const containerAspect = videoRect.width / videoRect.height;
                
                let overlayWidth, overlayHeight;
                
                if (videoAspect > containerAspect) {
                    // Video lebih lebar, fit to width
                    overlayWidth = videoRect.width;
                    overlayHeight = videoRect.width / videoAspect;
                } else {
                    // Video lebih tinggi, fit to height
                    overlayHeight = videoRect.height;
                    overlayWidth = videoRect.height * videoAspect;
                }
                
                overlay.width = overlayWidth;
                overlay.height = overlayHeight;
                
                // Center overlay
                overlay.style.position = 'absolute';
                overlay.style.left = ((videoRect.width - overlayWidth) / 2) + 'px';
                overlay.style.top = ((videoRect.height - overlayHeight) / 2) + 'px';
            }
        }
        
        // ==================== MANUAL PAGE FUNCTIONS ====================
        async function searchByNIM() {
            const nimInput = document.getElementById('nimInput');
            const nim = nimInput.value.trim();
            const resultDiv = document.getElementById('studentResult');
            const errorDiv = document.getElementById('studentError');
            const photoImg = document.getElementById('studentPhoto');
            const infoDiv = document.getElementById('studentInfo');
            
            // Hide previous results
            resultDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            
            if (!nim) {
                errorDiv.textContent = 'Silakan masukkan NIM';
                errorDiv.style.display = 'block';
                return;
            }
            
            try {
                const response = await fetch(`/api/student/${nim}`);
                const data = await response.json();
                
                if (data.success && data.exists) {
                    // Display photo
                    photoImg.src = data.photo_url || `/api/photo/${nim}`;
                    infoDiv.textContent = `NIM: ${data.nim}`;
                    resultDiv.style.display = 'block';
                } else {
                    errorDiv.textContent = data.message || `Mahasiswa dengan NIM ${nim} tidak ditemukan`;
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error searching student:', error);
                errorDiv.textContent = 'Terjadi kesalahan saat mencari mahasiswa';
                errorDiv.style.display = 'block';
            }
        }
        
        // Allow Enter key to search
        document.addEventListener('DOMContentLoaded', () => {
            const nimInput = document.getElementById('nimInput');
            if (nimInput) {
                nimInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        searchByNIM();
                    }
                });
            }
        });
        
        // ==================== REGISTER PAGE FUNCTIONS ====================
        // State Machine
        const RegisterState = {
            IDLE: "idle",
            SCANNING: "scanning",
            CAPTURED: "captured",
            SAVING: "saving",
            SUCCESS: "success",
            ERROR: "error"
        };
        
        let registerState = RegisterState.IDLE;
        
        function setRegisterState(state) {
            registerState = state;
            console.log("[REGISTER STATE]", state);
            updateRegisterButtons();
            updateRegisterStepIndicator();
        }
        
        function updateRegisterButtons() {
            // Note: btnSaveRegister is in modal, will be handled separately
        }
        
        function updateRegisterStepIndicator() {
            const steps = document.querySelectorAll('.register-step');
            steps.forEach((step, index) => {
                step.classList.remove('active', 'completed');
                
                if (registerState === RegisterState.IDLE) {
                    if (index === 0) step.classList.add('active');
                } else if (registerState === RegisterState.SCANNING) {
                    if (index === 1) step.classList.add('active');
                    if (index === 0) step.classList.add('completed');
                } else if (registerState === RegisterState.CAPTURED) {
                    if (index === 2) step.classList.add('active');
                    if (index < 2) step.classList.add('completed');
                } else if (registerState === RegisterState.SAVING) {
                    if (index === 2) step.classList.add('active');
                    if (index < 2) step.classList.add('completed');
                } else if (registerState === RegisterState.SUCCESS) {
                    step.classList.add('completed');
                }
            });
        }
        
        let registerPhotoBlob = null;
        let registerPhotoFile = null;
        let registerQCCheckLoop = null;
        let registerPhotoCaptured = false;
        
        // Liveness Detection State
        let registerFaceHistory = []; // Track face positions untuk motion detection
        let registerBlinkHistory = []; // Track eye landmarks untuk blink detection
        let registerMotionDetected = false;
        let registerBlinkDetected = false;
        const REGISTER_FACE_HISTORY_MAX = 10;
        const REGISTER_MOTION_THRESHOLD = 10; // pixels
        const REGISTER_BLINK_THRESHOLD = 0.15; // ratio change
        
        // Temporal Smoothing untuk Register (sama seperti Home page)
        let lastRegisterFaceData = null;
        let lastRegisterFaceTime = 0;
        const REGISTER_FACE_TIMEOUT = 800; // ms: keep last box for a short time (sama dengan home)
        
        // Voting mechanism untuk auto-capture (harus pass beberapa kali berturut-turut)
        let registerReadyHistory = []; // Track ready states (QC + liveness pass)
        const REGISTER_READY_VOTES_REQUIRED = 3; // Harus pass 3 kali berturut-turut
        
        // Store best frame untuk capture (frame terakhir yang pass semua check)
        let registerBestFrameBlob = null;
        
        
        // Start face detection untuk register - sama persis dengan home
        function startRegisterFaceDetection() {
            // Stop existing detection
            stopRegisterFaceDetection();
            
            let lastDetectionTime = 0;
            const DETECTION_INTERVAL = 100; // 100ms = 10 FPS untuk detection (lebih smooth)
            
            // Use requestAnimationFrame untuk lebih smooth
            function detectLoop() {
                // Pastikan loop terus berjalan - tidak ada kondisi yang membuatnya berhenti
                const overlay = document.getElementById('registerFaceOverlay');
                const registerVideo = document.getElementById('registerVideo');
                
                // Cek apakah masih di register page dan video masih aktif
                if (!registerVideo || !registerVideo.videoWidth || !registerVideo.videoHeight) {
                    // Video tidak ready, tunggu sebentar lalu coba lagi
                    registerQCCheckLoop = requestAnimationFrame(detectLoop);
                    return;
                }
                
                // Update overlay size secara berkala (sama seperti home)
                if (overlay) {
                    updateRegisterOverlaySize();
                }
                
                const now = Date.now();
                
                // Always render last known face box to avoid flicker (even if no new detection yet)
                if (overlay && registerVideo && lastRegisterFaceData && (now - lastRegisterFaceTime) < REGISTER_FACE_TIMEOUT) {
                    drawRegisterFaceBox(lastRegisterFaceData, registerVideo, overlay);
                } else if (overlay && lastRegisterFaceData && (now - lastRegisterFaceTime) >= REGISTER_FACE_TIMEOUT) {
                    // Only clear after timeout (not per-frame)
                    clearRegisterFaceBox(overlay);
                    lastRegisterFaceData = null;
                }
                
                // Run detection requests periodically - terus berjalan tanpa kondisi yang menghentikan
                // Tidak ada kondisi yang membuat detection berhenti - terus berjalan seperti di home
                if (now - lastDetectionTime >= DETECTION_INTERVAL && !isDetecting) {
                    lastDetectionTime = now;
                    detectRegisterFaceInFrame();
                }
                
                // Pastikan loop terus berjalan - tidak pernah berhenti
                registerQCCheckLoop = requestAnimationFrame(detectLoop);
            }
            
            registerQCCheckLoop = requestAnimationFrame(detectLoop);
        }
        
        function stopRegisterFaceDetection() {
            if (registerQCCheckLoop) {
                cancelAnimationFrame(registerQCCheckLoop);
                registerQCCheckLoop = null;
            }
            isDetecting = false;
            const overlay = document.getElementById('registerFaceOverlay');
            clearRegisterFaceBox(overlay);
            lastRegisterFaceData = null;
            lastRegisterFaceTime = 0;
        }
        
        // Detect face in register frame - sama persis dengan home
        async function detectRegisterFaceInFrame() {
            const registerVideo = document.getElementById('registerVideo');
            const registerCanvas = document.getElementById('registerCanvas');
            const overlay = document.getElementById('registerFaceOverlay');
            
            // Skip if video not ready or still processing
            if (!registerVideo || !registerVideo.videoWidth || !registerVideo.videoHeight || isDetecting) {
                return;
            }
            
            isDetecting = true;
            
            try {
                // OPTIMIZATION: Resize canvas untuk detection lebih cepat
                // Detection tidak perlu full resolution, cukup 320x240 atau max 640px
                const maxSize = 640;
                let canvasWidth = registerVideo.videoWidth;
                let canvasHeight = registerVideo.videoHeight;
                let scale = 1;
                
                if (canvasWidth > maxSize || canvasHeight > maxSize) {
                    scale = Math.min(maxSize / canvasWidth, maxSize / canvasHeight);
                    canvasWidth = Math.floor(canvasWidth * scale);
                    canvasHeight = Math.floor(canvasHeight * scale);
                }
                
                // Draw video frame to canvas (resized)
                const ctx = registerCanvas.getContext('2d');
                registerCanvas.width = canvasWidth;
                registerCanvas.height = canvasHeight;
                ctx.drawImage(registerVideo, 0, 0, canvasWidth, canvasHeight);
                
                // Convert to blob with lower quality untuk lebih cepat
                registerCanvas.toBlob(async (blob) => {
                    if (!blob) {
                        isDetecting = false;
                        return;
                    }
                    
                    try {
                        const formData = new FormData();
                        formData.append('image', blob, 'frame.jpg');
                        // Send original dimensions untuk scale bbox
                        formData.append('width', registerVideo.videoWidth);
                        formData.append('height', registerVideo.videoHeight);
                        
                        const response = await fetch('/detect-face', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            if (data.success && data.face) {
                                // Update persistence state
                                lastRegisterFaceData = data.face;
                                lastRegisterFaceTime = Date.now();
                                drawRegisterFaceBox(lastRegisterFaceData, registerVideo, overlay);
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
        
        async function checkRegisterFrameQC() {
            const registerVideo = document.getElementById('registerVideo');
            const registerCanvas = document.getElementById('registerCanvas');
            
            if (!registerVideo || !registerVideo.videoWidth || !registerVideo.videoHeight) {
                return;
            }
            
            try {
                // Capture frame
                const ctx = registerCanvas.getContext('2d');
                registerCanvas.width = registerVideo.videoWidth;
                registerCanvas.height = registerVideo.videoHeight;
                ctx.drawImage(registerVideo, 0, 0);
                
                // Convert to blob
                registerCanvas.toBlob(async (blob) => {
                    if (!blob) return;
                    
                    try {
                        // First, detect face untuk visual feedback
                        const detectFormData = new FormData();
                        detectFormData.append('image', blob, 'frame.jpg');
                        detectFormData.append('width', registerVideo.videoWidth);
                        detectFormData.append('height', registerVideo.videoHeight);
                        
                        const detectResponse = await fetch('/detect-face', {
                            method: 'POST',
                            body: detectFormData
                        });
                        
                        if (detectResponse.ok) {
                            const detectData = await detectResponse.json();
                            if (detectData.success && detectData.face) {
                                // Update temporal smoothing state
                                lastRegisterFaceData = detectData.face;
                                lastRegisterFaceTime = Date.now();
                                
                                // Draw face box (will be rendered in detection loop)
                                
                                // Update liveness detection
                                updateLivenessDetection(detectData.face);
                                
                                // Check QC jika face detected
                                const qcFormData = new FormData();
                                qcFormData.append('image', blob, 'frame.jpg');
                                
                                const qcResponse = await fetch('/api/check-qc', {
                                    method: 'POST',
                                    body: qcFormData
                                });
                                
                                if (qcResponse.ok) {
                                    const qcData = await qcResponse.json();
                                    
                                    if (qcData.qc_pass) {
                                        // Check liveness
                                        if (registerMotionDetected && registerBlinkDetected) {
                                            // Both QC and liveness passed - add to voting history
                                            registerReadyHistory.push(true);
                                            if (registerReadyHistory.length > REGISTER_READY_VOTES_REQUIRED) {
                                                registerReadyHistory.shift();
                                            }
                                            
                                            // Check if we have enough votes
                                            if (registerReadyHistory.length >= REGISTER_READY_VOTES_REQUIRED && 
                                                registerReadyHistory.every(v => v === true)) {
                                                // Stable ready state - store this frame as best
                                                registerBestFrameBlob = blob;
                                                // Auto capture setelah delay kecil untuk memastikan frame stabil
                                                setTimeout(() => {
                                                    if (registerBestFrameBlob && !registerPhotoCaptured) {
                                                        updateRegisterStatus('✅ Foto siap - Mengambil foto...');
                                                        autoCaptureRegisterPhoto(registerBestFrameBlob);
                                                    }
                                                }, 300); // Delay 300ms untuk memastikan frame benar-benar stabil
                                            } else {
                                                // Store current frame sebagai candidate jika belum ada
                                                if (!registerBestFrameBlob) {
                                                    registerBestFrameBlob = blob;
                                                }
                                                updateRegisterStatus(`Kualitas baik - Memeriksa stabilitas... (${registerReadyHistory.length}/${REGISTER_READY_VOTES_REQUIRED})`);
                                            }
                                        } else {
                                            // Reset voting history jika liveness belum pass
                                            registerReadyHistory = [];
                                            
                                            // Show liveness progress
                                            let progressMsg = 'Kualitas baik - ';
                                            if (!registerMotionDetected && !registerBlinkDetected) {
                                                progressMsg += 'Gerakkan kepala dan kedipkan mata';
                                            } else if (!registerMotionDetected) {
                                                progressMsg += 'Gerakkan kepala';
                                            } else if (!registerBlinkDetected) {
                                                progressMsg += 'Kedipkan mata';
                                            }
                                            updateRegisterStatus(progressMsg);
                                        }
                                    } else {
                                        // QC failed - reset voting history dan best frame
                                        registerReadyHistory = [];
                                        registerBestFrameBlob = null;
                                        updateRegisterStatus('Wajah terdeteksi - ' + (qcData.user_message || 'Memeriksa kualitas...'));
                                    }
                                }
                            } else {
                                // No face detected - update temporal smoothing
                                if ((Date.now() - lastRegisterFaceTime) >= REGISTER_FACE_TIMEOUT) {
                                    lastRegisterFaceData = null;
                                    updateRegisterStatus('Mencari wajah...');
                                }
                                // Don't clear immediately - let temporal smoothing handle it
                            }
                        }
                    } catch (err) {
                        console.error('Error checking QC:', err);
                    }
                }, 'image/jpeg', 0.7);
            } catch (err) {
                console.error('Error in checkRegisterFrameQC:', err);
            }
        }
        
        function updateLivenessDetection(faceData) {
            const bbox = faceData.bbox;
            const centerX = (bbox[0] + bbox[2]) / 2;
            const centerY = (bbox[1] + bbox[3]) / 2;
            
            // Motion Detection: Track face center position
            registerFaceHistory.push({ x: centerX, y: centerY, time: Date.now() });
            if (registerFaceHistory.length > REGISTER_FACE_HISTORY_MAX) {
                registerFaceHistory.shift();
            }
            
            if (registerFaceHistory.length >= 3) {
                // Calculate variance in position
                const positions = registerFaceHistory.slice(-5); // Last 5 positions
                const xs = positions.map(p => p.x);
                const ys = positions.map(p => p.y);
                const meanX = xs.reduce((a, b) => a + b, 0) / xs.length;
                const meanY = ys.reduce((a, b) => a + b, 0) / ys.length;
                const varianceX = xs.reduce((sum, x) => sum + Math.pow(x - meanX, 2), 0) / xs.length;
                const varianceY = ys.reduce((sum, y) => sum + Math.pow(y - meanY, 2), 0) / ys.length;
                const totalVariance = Math.sqrt(varianceX + varianceY);
                
                if (totalVariance > REGISTER_MOTION_THRESHOLD) {
                    registerMotionDetected = true;
                }
            }
            
            // Blink Detection: Simplified approach
            // Track face detection confidence variation as proxy for blink
            // When eyes blink, detection confidence may slightly drop
            registerBlinkHistory.push({
                confidence: faceData.confidence || 0.9,
                time: Date.now()
            });
            
            if (registerBlinkHistory.length > REGISTER_FACE_HISTORY_MAX) {
                registerBlinkHistory.shift();
            }
            
            // Detect blink: look for confidence drops (simulating eye closure)
            if (registerBlinkHistory.length >= 5 && !registerBlinkDetected) {
                const confidences = registerBlinkHistory.map(h => h.confidence);
                const maxConf = Math.max(...confidences);
                const minConf = Math.min(...confidences);
                const confRange = maxConf - minConf;
                
                // If confidence varies significantly, it might indicate blinking
                // Also require motion to be detected first
                if (registerMotionDetected && confRange > 0.05) {
                    registerBlinkDetected = true;
                }
            }
            
            // Alternative: If motion detected for sufficient time, assume liveness
            // (This is a fallback if blink detection doesn't trigger)
            if (registerMotionDetected && registerFaceHistory.length >= 8 && !registerBlinkDetected) {
                // After enough motion frames, consider it live even without explicit blink
                registerBlinkDetected = true;
            }
        }
        
        // Draw face box untuk register - sama persis dengan home
        function drawRegisterFaceBox(faceData, video, overlay) {
            if (!overlay || !video) return;
            
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
            const labelHeight = 28;
            const labelX = Math.max(0, Math.min(x, overlay.width - labelWidth));
            const labelY = Math.max(labelHeight, y - 8);
            
            // Draw rounded rectangle for label
            ctx.beginPath();
            ctx.roundRect(labelX, labelY - labelHeight, labelWidth, labelHeight, 8);
            ctx.fill();
            
            // Draw text
            ctx.fillStyle = 'white';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(labelText, labelX + 12, labelY - labelHeight / 2);
        }
        
        function clearRegisterFaceBox(overlay) {
            if (!overlay) {
                overlay = document.getElementById('registerFaceOverlay');
            }
            if (overlay) {
                const ctx = overlay.getContext('2d');
                ctx.clearRect(0, 0, overlay.width, overlay.height);
            }
        }
        
        function validateNIM() {
            const nimInput = document.getElementById('registerNIMInput');
            const nim = nimInput.value.trim();
            
            if (!nim) {
                updateRegisterStatus('❌ Silakan masukkan NIM', 'error');
                setRegisterState(RegisterState.ERROR);
                return false;
            }
            
            // Validate format: 8-15 digits
            if (!/^\d{8,15}$/.test(nim)) {
                updateRegisterStatus('❌ Format NIM tidak valid (harus 8-15 digit)', 'error');
                setRegisterState(RegisterState.ERROR);
                return false;
            }
            
            return true;
        }
        
        function autoCaptureRegisterPhoto(bestFrameBlob = null) {
            // Prevent multiple captures
            if (registerPhotoCaptured) return;
            
            // Mark as captured immediately to prevent race condition
            registerPhotoCaptured = true;
            
            // Use best frame jika tersedia, atau capture dari video
            if (bestFrameBlob || registerBestFrameBlob) {
                const blobToUse = bestFrameBlob || registerBestFrameBlob;
                registerPhotoBlob = blobToUse;
                registerPhotoFile = null;
                
                // Stop auto-capture loop
                if (registerQCCheckLoop) {
                    cancelAnimationFrame(registerQCCheckLoop);
                    registerQCCheckLoop = null;
                }
                
                // Set state to captured
                setRegisterState(RegisterState.CAPTURED);
                
                // Show modal dengan preview foto
                showRegisterModal(blobToUse);
                
                // Reset best frame
                registerBestFrameBlob = null;
                return;
            }
            
            // Fallback: capture dari video langsung
            const registerVideo = document.getElementById('registerVideo');
            const registerCanvas = document.getElementById('registerCanvas');
            
            if (!registerVideo || !registerVideo.videoWidth || !registerVideo.videoHeight) {
                registerPhotoCaptured = false; // Reset if failed
                return;
            }
            
            try {
                const ctx = registerCanvas.getContext('2d');
                registerCanvas.width = registerVideo.videoWidth;
                registerCanvas.height = registerVideo.videoHeight;
                ctx.drawImage(registerVideo, 0, 0);
                
                // Use high quality untuk foto yang bagus untuk face recognition
                registerCanvas.toBlob(blob => {
                    if (blob) {
                        registerPhotoBlob = blob;
                        registerPhotoFile = null;
                        
                        // Stop auto-capture loop
                        if (registerQCCheckLoop) {
                            cancelAnimationFrame(registerQCCheckLoop);
                            registerQCCheckLoop = null;
                        }
                        
                        // Update button
                        // Show modal dengan preview foto
                        showRegisterModal(blob);
                    } else {
                        registerPhotoCaptured = false; // Reset if failed
                        updateRegisterStatus('❌ Gagal mengambil foto');
                    }
                }, 'image/jpeg', 0.95); // High quality (0.95) untuk foto yang bagus
            } catch (err) {
                console.error('Error auto-capturing photo:', err);
                registerPhotoCaptured = false; // Reset if failed
                updateRegisterStatus('❌ Gagal mengambil foto');
            }
        }
        
        function updateRegisterStatus(message, severity = null) {
            const statusInfo = document.getElementById('registerStatusInfo');
            if (statusInfo) {
                statusInfo.textContent = message;
                
                // Map severity to color (if provided), otherwise use emoji-based detection
                if (severity === 'error' || message.includes('❌')) {
                    statusInfo.style.background = 'rgba(245, 101, 101, 0.1)';
                    statusInfo.style.color = '#f56565';
                } else if (severity === 'warning' || message.includes('⚠️')) {
                    statusInfo.style.background = 'rgba(237, 137, 54, 0.1)';
                    statusInfo.style.color = '#ed8936';
                } else if (severity === 'info' || message.includes('✅')) {
                    statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                    statusInfo.style.color = '#667eea';
                } else if (message.includes('✅')) {
                    statusInfo.style.background = 'rgba(72, 187, 120, 0.1)';
                    statusInfo.style.color = '#48bb78';
                } else {
                    statusInfo.style.background = 'rgba(102, 126, 234, 0.1)';
                    statusInfo.style.color = '#667eea';
                }
            }
        }
        
        function uploadPhotoForRegister(event) {
            // Validate NIM first
            if (!validateNIM()) {
                event.target.value = ''; // Clear file input
                return;
            }
            
            const file = event.target.files[0];
            if (file) {
                // Reset all state
                registerPhotoFile = file;
                registerPhotoBlob = null;
                registerPhotoCaptured = true; // Mark as captured
                registerBestFrameBlob = null;
                registerReadyHistory = [];
                
                setRegisterState(RegisterState.CAPTURED);
                showRegisterModal(file);
                updateRegisterStatus('✅ Foto siap - Klik Simpan ke Database');
            }
        }
        
        function showRegisterModal(source) {
            const overlay = document.getElementById('registerModalOverlay');
            const img = document.getElementById('registerModalImg');
            
            if (!overlay || !img) return;
            
            // Create object URL dari blob atau file
            if (source instanceof File) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    img.src = e.target.result;
                    overlay.classList.add('active');
                };
                reader.readAsDataURL(source);
            } else if (source instanceof Blob) {
                const url = URL.createObjectURL(source);
                img.src = url;
                overlay.classList.add('active');
            } else if (typeof source === 'string') {
                img.src = source;
                overlay.classList.add('active');
            }
        }
        
        function closeRegisterModal() {
            const overlay = document.getElementById('registerModalOverlay');
            if (overlay) {
                overlay.classList.remove('active');
                
                // Cleanup object URL jika ada
                const img = document.getElementById('registerModalImg');
                if (img && img.src.startsWith('blob:')) {
                    URL.revokeObjectURL(img.src);
                }
            }
        }
        
        function closeRegisterModalOutside(event) {
            if (event.target.id === 'registerModalOverlay') {
                closeRegisterModal();
            }
        }
        
        function retryRegisterCapture() {
            // Close modal
            closeRegisterModal();
            
            // Reset state
            registerPhotoCaptured = false;
            registerPhotoBlob = null;
            registerPhotoFile = null;
            registerBestFrameBlob = null;
            registerReadyHistory = [];
            
            // Clear face overlay
            clearRegisterFaceBox();
            lastRegisterFaceData = null;
            lastRegisterFaceTime = 0;
            
            // Set state back to idle
            setRegisterState(RegisterState.IDLE);
            
            // Update status
            updateRegisterStatus('Siap untuk capture ulang');
        }
        
        function saveRegisterPhoto() {
            // Close modal first
            closeRegisterModal();
            
            // Call existing registerPhoto function
            registerPhoto();
        }
        
        // Legacy function untuk backward compatibility (redirect ke modal)
        function previewRegisterPhoto(source) {
            showRegisterModal(source);
        }
        
        async function registerPhoto() {
            // Validate NIM
            if (!validateNIM()) {
                return;
            }
            
            // Check if already saving
            if (registerState === RegisterState.SAVING) {
                return; // Prevent double submit
            }
            
            const nimInput = document.getElementById('registerNIMInput');
            const nim = nimInput.value.trim();
            const statusDiv = document.getElementById('registerStatus');
            const btnSave = document.getElementById('btnSaveRegister');
            
            statusDiv.style.display = 'none';
            
            if (!registerPhotoBlob && !registerPhotoFile) {
                statusDiv.textContent = 'Silakan ambil atau upload foto terlebih dahulu';
                statusDiv.className = 'status-message error';
                statusDiv.style.display = 'block';
                setRegisterState(RegisterState.ERROR);
                return;
            }
            
            // Set state to saving
            setRegisterState(RegisterState.SAVING);
            
            if (btnSave) {
                btnSave.disabled = true;
                btnSave.textContent = '⏳ Menyimpan...';
            }
            
            try {
                const formData = new FormData();
                formData.append('nim', nim);
                
                if (registerPhotoFile) {
                    formData.append('image', registerPhotoFile);
                } else if (registerPhotoBlob) {
                    formData.append('image', registerPhotoBlob, 'photo.jpg');
                }
                
                const response = await fetch('/api/register', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    setRegisterState(RegisterState.SUCCESS);
                    
                    statusDiv.textContent = `✅ Berhasil! Foto mahasiswa dengan NIM ${nim} telah diregistrasi`;
                    statusDiv.className = 'status-message success';
                    statusDiv.style.display = 'block';
                    
                    // Update status info
                    updateRegisterStatus(`✅ Foto NIM ${nim} berhasil disimpan`);
                    
                    // Reset form dan state
                    nimInput.value = '';
                    registerPhotoBlob = null;
                    registerPhotoFile = null;
                    registerPhotoCaptured = false;
                    registerBestFrameBlob = null;
                    registerReadyHistory = [];
                    document.getElementById('registerFileInput').value = '';
                    
                    // Clear face overlay
                    clearRegisterFaceBox();
                    lastRegisterFaceData = null;
                    lastRegisterFaceTime = 0;
                    
                    // Reset to idle after 2 seconds
                    setTimeout(() => {
                        setRegisterState(RegisterState.IDLE);
                    }, 2000);
                } else {
                    setRegisterState(RegisterState.ERROR);
                    statusDiv.textContent = data.message || data.error || 'Gagal menyimpan foto';
                    statusDiv.className = 'status-message error';
                    statusDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error registering photo:', error);
                setRegisterState(RegisterState.ERROR);
                statusDiv.textContent = 'Terjadi kesalahan saat menyimpan foto: ' + error.message;
                statusDiv.className = 'status-message error';
                statusDiv.style.display = 'block';
            } finally {
                if (btnSave) {
                    btnSave.disabled = false;
                    btnSave.textContent = '💾 Simpan ke Database';
                }
            }
        }
        
        // ==================== ADMIN PAGE FUNCTIONS ====================
        async function deleteNIM() {
            const nimInput = document.getElementById('adminNIMInput');
            const statusDiv = document.getElementById('adminStatus');
            const btnDelete = document.getElementById('btnDeleteNIM');
            
            const nim = nimInput.value.trim();
            
            // Validate NIM
            if (!nim) {
                statusDiv.textContent = '❌ Silakan masukkan NIM';
                statusDiv.className = 'status-message error';
                statusDiv.style.display = 'block';
                return;
            }
            
            // Validate NIM format (8-15 digits)
            if (!/^\d{8,15}$/.test(nim)) {
                statusDiv.textContent = '❌ Format NIM tidak valid (harus 8-15 digit)';
                statusDiv.className = 'status-message error';
                statusDiv.style.display = 'block';
                return;
            }
            
            // Confirm deletion
            if (!confirm(`Apakah Anda yakin ingin menghapus NIM ${nim} dari database?\n\nTindakan ini tidak dapat dibatalkan!`)) {
                return;
            }
            
            // Disable button
            if (btnDelete) {
                btnDelete.disabled = true;
                btnDelete.textContent = '⏳ Menghapus...';
            }
            
            statusDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/admin/delete-nim', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ nim: nim })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.textContent = `✅ ${data.message || `NIM ${nim} berhasil dihapus dari database`}`;
                    statusDiv.className = 'status-message success';
                    statusDiv.style.display = 'block';
                    
                    // Clear input
                    nimInput.value = '';
                } else {
                    statusDiv.textContent = `❌ ${data.error || data.message || 'Gagal menghapus NIM'}`;
                    statusDiv.className = 'status-message error';
                    statusDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Error deleting NIM:', error);
                statusDiv.textContent = '❌ Terjadi kesalahan saat menghapus NIM: ' + error.message;
                statusDiv.className = 'status-message error';
                statusDiv.style.display = 'block';
            } finally {
                if (btnDelete) {
                    btnDelete.disabled = false;
                    btnDelete.textContent = '🗑️ Hapus NIM dari Database';
                }
            }
        }
    </script>
</body>
</html>
"""

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
        from face_recognition.database import FaceDatabase
        db = FaceDatabase()
        
        # Check if exists
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

