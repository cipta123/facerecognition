# Cara Kerja Face Recognition System

## Flow Diagram

```
1. User Akses Web Interface
   ↓
2. Browser Request Camera Access (HTTPS required untuk IP)
   ↓
3. User Klik "Ambil Foto"
   ↓
4. JavaScript Capture Frame dari Video
   ↓
5. Convert ke Blob (JPEG)
   ↓
6. POST ke /recognize API
   ↓
7. Server: Load Image → Preprocess → Generate Embedding
   ↓
8. Server: Search di Database (Cosine Similarity)
   ↓
9. Server: Return NIM + Confidence
   ↓
10. Browser: Display Result
```

## Detail Proses

### 1. Capture Foto (Client-side)

```javascript
// User klik "Ambil Foto"
capturePhoto() {
  - Ambil frame dari video element
  - Draw ke canvas
  - Convert canvas ke Blob (JPEG)
  - Kirim ke API via FormData
}
```

### 2. API Processing (Server-side)

```python
POST /recognize
  ↓
1. Receive image (FormData atau Base64)
  ↓
2. Convert ke PIL Image → NumPy Array (BGR)
  ↓
3. Preprocess:
   - RetinaFace Detection (detect wajah)
   - 5-Point Alignment
   - Crop & Resize ke 112x112
   - Normalize: (img - 127.5) / 128.0
   - RGB Conversion
  ↓
4. ArcFace Encoding:
   - Generate 512-D embedding
   - L2 Normalize
  ↓
5. Database Search:
   - Cosine similarity dengan semua embeddings
   - Filter: confidence >= threshold (0.55)
   - Sort by confidence (descending)
   - Return top matches
  ↓
6. Log ke Database:
   - Save recognition log (NIM, confidence, timestamp)
  ↓
7. Return JSON Response
```

### 3. Display Result (Client-side)

```javascript
// Receive response dari API
if (success) {
  - Display: NIM + Confidence Score
  - Green box (success)
} else {
  - Display: Error message
  - Red box (error)
}
```

## Troubleshooting

### Klik "Ambil Foto" Tidak Ada Response

**Cek Browser Console (F12):**
1. Buka Developer Tools (F12)
2. Tab "Console"
3. Lihat error messages

**Kemungkinan Masalah:**

1. **Video belum ready**
   - Tunggu 1-2 detik setelah page load
   - Pastikan kamera sudah muncul di video element

2. **API Error**
   - Cek Network tab di Developer Tools
   - Lihat request ke `/recognize`
   - Cek response status code

3. **No face detected**
   - Pastikan wajah jelas terlihat
   - Pastikan lighting cukup
   - Coba dengan foto yang sudah ada di database

4. **Database kosong**
   - Pastikan sudah run batch encoder
   - Cek: `python test_recognition.py`

## Testing Manual

### Test 1: Cek API Langsung

```bash
# Test dengan curl
curl -X POST https://10.22.10.131:5000/recognize \
  -F "image=@output/photos/857264993.jpg" \
  -k
```

### Test 2: Cek Database

```bash
python test_recognition.py
```

### Test 3: Cek Console Browser

1. Buka web interface
2. Tekan F12 (Developer Tools)
3. Tab "Console"
4. Klik "Ambil Foto"
5. Lihat log messages

## Expected Console Output

```
Video ready: 640 x 480
Capture photo clicked
Image captured, converting to blob...
Blob created, size: 45234 bytes
Sending image to API...
Sending POST request to /recognize...
Response status: 200
Response data: {success: true, nim: "857264993", confidence: 0.95}
```

## Common Errors

### "Video not ready"
- **Solusi**: Tunggu beberapa detik, pastikan kamera sudah aktif

### "Server error: 500"
- **Solusi**: Cek server logs, pastikan database connected

### "No face detected"
- **Solusi**: Pastikan wajah jelas, coba dengan foto lain

### "No match found"
- **Solusi**: Pastikan foto sudah di-encode ke database

