# SRS5G Photo Scraper

Aplikasi untuk mengunduh foto mahasiswa dari SRS5G (srs5g.ut.ac.id) secara otomatis menggunakan Playwright.

## Fitur

- **Response Interception**: Menangkap image bytes langsung dari XHR response (lebih cepat dan stabil)
- **Resume Capability**: Jika terhenti, akan melanjutkan dari NIM terakhir (tidak mengulang dari awal)
- **Skip Existing**: Tidak akan download ulang foto yang sudah ada
- **Progress Tracking**: Real-time progress saving ke `progress.json`
- **Error Logging**: Log semua error ke `error.txt` dengan timestamp
- **Progress Bar**: Visual progress dengan tqdm

## Instalasi

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Setup Credentials

Buat file `.env` di root folder dengan isi:

```
SRS_USERNAME=username_anda
SRS_PASSWORD=password_anda
```

### 4. Siapkan Daftar NIM

Edit file `nim_list.csv` dengan daftar NIM yang ingin di-scrape:

```csv
nim
857264993
857264994
857264995
...
```

## Penggunaan

### Basic Usage

```bash
python scraper.py
```

### Custom CSV File

```bash
python scraper.py --csv path/to/your/nim_list.csv
```

### Visible Browser (untuk debugging)

```bash
python scraper.py --visible
```

## Output

```
output/
├── photos/         # Folder berisi foto yang diunduh ({nim}.jpg)
├── progress.json   # Progress tracking (untuk resume)
└── error.txt       # Log error
```

## Resume & Skip Behavior

### Resume
- Jika aplikasi terhenti (Ctrl+C, error, dll), cukup jalankan ulang
- Aplikasi akan membaca `progress.json` dan melanjutkan dari NIM yang belum selesai
- **Tidak akan mengulang dari awal**

### Skip Existing
- Sebelum download, aplikasi cek apakah `photos/{nim}.jpg` sudah ada
- Jika sudah ada, skip dan lanjut ke NIM berikutnya
- Berguna jika menambah NIM baru ke CSV

## Performance

- ~2-3 detik per NIM (termasuk delay)
- 20,000 NIM ≈ 11-17 jam (sequential)
- Bisa dijalankan di background (headless mode)

## Troubleshooting

### Login Gagal
- Periksa username dan password di `.env`
- Coba dengan `--visible` untuk melihat browser

### Button "Lihat" Tidak Ditemukan
- Halaman mungkin berubah, perlu update selector di `config.py`
- Cek apakah NIM valid dan memiliki foto

### Timeout Error
- Koneksi internet lambat
- Increase timeout di `config.py`

## Struktur File

```
scrapper/
├── scraper.py          # Main scraper script
├── config.py           # Configuration settings
├── utils.py            # Helper functions
├── requirements.txt    # Python dependencies
├── .env                # Credentials (gitignored)
├── .gitignore          # Git ignore rules
├── nim_list.csv        # Daftar NIM
├── README.md           # Documentation
└── output/
    ├── photos/         # Downloaded photos
    ├── progress.json   # Progress tracking
    └── error.txt       # Error log
```

## License

MIT

