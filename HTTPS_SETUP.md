# Setup HTTPS untuk Akses Kamera via LAN

## Masalah
Browser memerlukan HTTPS untuk akses kamera via IP address (bukan localhost).

## Solusi

### Opsi 1: Setup HTTPS (Recommended untuk Production)

1. **Install cryptography library:**
   ```bash
   pip install cryptography
   ```

2. **Generate self-signed certificate:**
   ```bash
   python setup_https.py
   ```

3. **Run dengan HTTPS:**
   ```bash
   python -m api.web_interface_https
   ```

4. **Akses di browser:**
   - `https://10.22.10.131:5000`
   - Browser akan warning tentang self-signed certificate
   - Klik "Advanced" → "Proceed to localhost" (atau "Accept the Risk")

### Opsi 2: Gunakan Upload Foto (Tidak Perlu HTTPS)

Web interface sudah support upload foto tanpa perlu kamera:

1. **Run server biasa (HTTP):**
   ```bash
   python -m api.web_interface
   ```

2. **Akses di browser:**
   - `http://10.22.10.131:5000`
   - Klik "📁 Upload Foto"
   - Pilih foto dari komputer
   - Sistem akan recognize wajah

### Opsi 3: Akses via Localhost (Development)

Jika akses dari server sendiri:
- `http://localhost:5000` - Kamera bisa diakses (localhost exception)
- `http://127.0.0.1:5000` - Kamera bisa diakses

## Catatan

- **HTTPS wajib** untuk akses kamera via IP address (10.22.10.131)
- **HTTP cukup** untuk localhost atau upload foto
- **Self-signed certificate** hanya untuk development/testing
- **Production**: Gunakan certificate dari CA (Let's Encrypt, dll)

## Troubleshooting

### Kamera tidak muncul
- Pastikan izin kamera sudah diberikan di browser
- Cek apakah browser support getUserMedia
- Gunakan opsi Upload Foto sebagai alternatif

### HTTPS certificate warning
- Ini normal untuk self-signed certificate
- Klik "Advanced" → "Proceed" untuk continue
- Untuk production, gunakan certificate dari CA

