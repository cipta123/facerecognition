# Face Recognition System dengan ArcFace

Sistem face recognition untuk verifikasi identitas mahasiswa saat ujian menggunakan ArcFace (InsightFace).

## Fitur

- ✅ **ArcFace dengan RetinaFace**: Detection dan recognition dengan akurasi tinggi
- ✅ **Multi-format Support**: JPG, PNG, JPEG (termasuk alpha channel)
- ✅ **PostgreSQL Database**: Scalable storage untuk embeddings
- ✅ **Web-based Interface**: Real-time camera capture untuk ujian
- ✅ **REST API**: Untuk integration dengan sistem lain
- ✅ **Batch Processing**: Process ribuan foto dengan progress tracking
- ✅ **Sample Mode**: Testing dengan sample files (termasuk cipta_anugrah.png)

## Instalasi

### 1. Install Dependencies

```bash
pip install -r requirements_face.txt
```

### 2. Setup PostgreSQL Database

Buat database PostgreSQL:

```sql
CREATE DATABASE face_recognition;
```

### 3. Setup Environment Variables

Copy `.env.example` ke `.env` dan isi:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=face_recognition
DB_USER=postgres
DB_PASSWORD=your_password
```

### 4. Download InsightFace Models

Models akan auto-download saat pertama kali run, atau download manual:

```bash
# Models akan disimpan di ~/.insightface/models/
```

## Penggunaan

### 1. Batch Encoding (Generate Embeddings)

#### Test dengan Sample (Recommended untuk pertama kali)

```bash
# Test dengan cipta_anugrah.png + beberapa JPG
python -m face_recognition.batch_encoder --files cipta_anugrah.png 857264993.jpg 836252898.jpg

# Test dengan random 50 foto
python -m face_recognition.batch_encoder --sample 50

# Process semua foto (11,000+)
python -m face_recognition.batch_encoder --all
```

#### Output

```
Processing 3 custom files...
Processing custom files: 100%|████████| 3/3 [00:15<00:00,  5.2s/it]

============================================================
PROCESSING STATISTICS
============================================================
Total files    : 3
Success        : 3
Failed         : 0
Skipped        : 0
============================================================
```

### 2. Start Web Interface

```bash
python -m api.web_interface
```

Akses di browser: `http://localhost:5000`

### 3. REST API

#### Start API Server

```bash
python -m api.recognition_api
```

#### Endpoints

**POST /recognize**
- Upload foto untuk recognition
- Multipart form: `image` file
- JSON: `{"image": "base64_string"}`

**GET /status**
- Check system status

**GET /stats**
- Get database statistics

#### Example Request

```bash
curl -X POST http://localhost:5000/recognize \
  -F "image=@photo.jpg"
```

#### Example Response

```json
{
  "success": true,
  "nim": "857264993",
  "confidence": 0.85,
  "matches": [
    {"nim": "857264993", "confidence": 0.85},
    {"nim": "857264994", "confidence": 0.45}
  ]
}
```

## Struktur File

```
scrapper/
├── face_recognition/
│   ├── __init__.py
│   ├── config.py              # Configuration
│   ├── preprocessor.py        # RetinaFace + Alignment + Normalization
│   ├── encoder.py             # ArcFace embedding generator
│   ├── database.py            # PostgreSQL handler
│   ├── matcher.py             # Cosine similarity matcher
│   └── batch_encoder.py       # Batch processing
├── api/
│   ├── __init__.py
│   ├── recognition_api.py     # REST API
│   └── web_interface.py       # Web UI
├── models/                    # InsightFace models (auto-download)
├── output/photos/             # Foto mahasiswa dari scraper
├── requirements_face.txt      # Dependencies
└── .env                       # Database credentials
```

## Configuration

Edit `face_recognition/config.py` untuk:

- **Threshold**: Cosine similarity threshold (default: 0.55)
- **Model**: ArcFace model (buffalo_l untuk ResNet100)
- **Input Size**: 112x112 (wajib untuk ArcFace)
- **Database**: PostgreSQL connection settings

## Pipeline ArcFace

1. **Load Image**: Support JPG, PNG (dengan alpha channel handling)
2. **RetinaFace Detection**: Detect wajah + 5 landmarks
3. **5-Point Alignment**: Align wajah
4. **Crop & Resize**: Crop → Resize ke 112x112
5. **Normalize**: (img - 127.5) / 128.0
6. **RGB Conversion**: BGR → RGB
7. **ArcFace Encoding**: Generate 512-D embedding
8. **Database Storage**: Save ke PostgreSQL
9. **Matching**: Cosine similarity search

## Troubleshooting

### Model tidak terdownload

```bash
# InsightFace akan auto-download, tapi jika gagal:
# Models location: ~/.insightface/models/
# Download manual dari: https://github.com/deepinsight/insightface
```

### PostgreSQL connection error

- Pastikan PostgreSQL running
- Check credentials di `.env`
- Test connection: `psql -h localhost -U postgres -d face_recognition`

### No face detected

- Pastikan foto memiliki wajah yang jelas
- Check RetinaFace confidence threshold di config
- Coba dengan foto yang lebih besar/resolusi lebih tinggi

### Low accuracy

- Tune threshold (0.5-0.6)
- Pastikan preprocessing pipeline benar
- Check apakah embedding sudah L2 normalized

## Performance

- **Encoding**: ~1-2 detik per foto (CPU)
- **Matching**: ~10-50ms per query (tergantung database size)
- **Batch Processing**: ~50-100 foto/menit (tergantung hardware)

## Next Steps

1. Test dengan sample files (cipta_anugrah.png + beberapa JPG)
2. Validate accuracy dengan known faces
3. Tune threshold berdasarkan test results
4. Process semua foto setelah validation OK
5. Deploy web interface untuk production

## License

MIT

