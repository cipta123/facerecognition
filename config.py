"""
Configuration settings for SRS5G Photo Scraper
"""
import os
from pathlib import Path

# Base URLs
BASE_URL = "https://srs5g.ut.ac.id"
LOGIN_URL = f"{BASE_URL}/auth/login"  # Updated: correct login path
STUDENT_INFO_URL = f"{BASE_URL}/sarjana-diploma/laporan/info-mahasiswa/edit-pemberkasan"

# Selectors
SELECTORS = {
    # Login page selectors
    "email": "input[type='email'], input[name='email'], input[placeholder*='Email'], input[id*='email']",
    "password": "input[type='password'], input[name='password']",
    "captcha_question": "text=/\\d+\\s*[+\\-×÷]\\s*\\d+/",  # Matches "8 + 0" pattern
    "captcha_input": "input[placeholder*='Jawaban'], input[placeholder*='jawaban']",
    "login_button": "button:has-text('Masuk'), button[type='submit']",
    
    # Student info page selectors
    "view_photo_button": "text=Lihat",  # Tombol "Lihat" untuk melihat foto
}

# Delays (in milliseconds)
DELAYS = {
    "after_login": 2000,
    "after_navigate": 500,
    "after_click": 1000,
    "between_requests": 300,
}

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PHOTOS_DIR = OUTPUT_DIR / "photos"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
ERROR_FILE = OUTPUT_DIR / "error.txt"
NIM_CSV_FILE = BASE_DIR / "nim_list.csv"

# Browser settings
HEADLESS = True
TIMEOUT = 30000  # 30 seconds

# Content types to intercept
IMAGE_CONTENT_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

