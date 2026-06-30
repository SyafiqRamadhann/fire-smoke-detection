# 🔥 Fire & Smoke Detection — YOLO11 Web App

Aplikasi web deteksi api dan asap real-time menggunakan model YOLO11.
Dibangun dengan FastAPI (backend) dan Bootstrap 5 (frontend).

## Fitur

- **Image Detection** — Upload gambar JPG/PNG, deteksi api & asap
- **Video Detection** — Upload video MP4/AVI, proses frame-by-frame
- **Live Detection** — Deteksi real-time via webcam (WebSocket)
- **Detection History** — Riwayat semua deteksi tersimpan di database
- **Dashboard** — Statistik total deteksi, confidence, FPS

## Prasyarat

- Python 3.10 atau 3.11
- pip
- File model `weights/best.pt` (lihat bagian Download Model)

## Instalasi

```bash
# 1. Clone proyek
git clone <url-proyek-anda>
cd fire-smoke-detection

# 2. Buat virtual environment
python -m venv venv

# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install dependency
pip install -r requirements.txt

# 4. Download model YOLO11
# Clone repository model:
git clone https://github.com/sayedgamal99/Real-Time-Smoke-Fire-Detection-YOLO11 temp_model
cp temp_model/models/best_nano_111.pt weights/best.pt
rm -rf temp_model

# 5. Salin file konfigurasi
cp .env .env.local   # edit jika perlu

# 6. Jalankan aplikasi
python main.py
```

Akses di browser: **http://localhost:8000**
Dokumentasi API : **http://localhost:8000/docs**

## Struktur Folder

```
fire-smoke-detection/
├── app/
│   ├── api/           # FastAPI endpoint routes
│   ├── services/      # Business logic & YOLO11 service
│   ├── models/        # Pydantic schemas
│   ├── database/      # SQLAlchemy ORM & CRUD
│   └── utils/         # File manager & OpenCV drawing
├── static/            # CSS, JS, images
├── templates/         # Jinja2 HTML templates
├── uploads/           # File yang diupload user (sementara)
├── outputs/           # File hasil deteksi
├── weights/           # Model YOLO11 (best.pt)
├── database/          # SQLite database file
├── main.py            # Entry point
├── config.py          # Konfigurasi global
└── requirements.txt
```

## Konfigurasi

Edit file `.env` untuk menyesuaikan:

```env
CONFIDENCE_THRESHOLD=0.35   # Threshold deteksi (0.0-1.0)
IOU_THRESHOLD=0.10           # IoU threshold
MAX_IMAGE_SIZE_MB=10         # Batas ukuran gambar
MAX_VIDEO_SIZE_MB=500        # Batas ukuran video
PORT=8000                    # Port server
```

## Informasi Model

Model: YOLO11 (best_nano_111.pt)  
Dataset: 10.463 gambar (Fire & Smoke)  
Kelas: Fire, Smoke

| Metrik     | Nilai  |
|-----------|--------|
| Precision | 80.6%  |
| Recall    | 71.7%  |
| mAP@50    | 77.0%  |
| FPS (GPU) | 30–60  |

## Deployment (VPS Linux)

```bash
# Install supervisor untuk process management
pip install gunicorn

# Jalankan dengan gunicorn + uvicorn workers
gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --timeout 120

# Gunakan nginx sebagai reverse proxy (opsional)
```

## Hasil Pengujian (Terverifikasi)

Pengujian dilakukan dengan model `best_nano_111.pt` asli dan data nyata dari repository sumber.

| Mode | Input | Hasil |
|------|-------|-------|
| Image | Rumah terbakar (house.png) | Fire 83%, Smoke 62% — bbox akurat |
| Image | Petugas damkar di hutan (fire14.png) | Smoke 36% — bbox akurat |
| Video | Klip 3 detik (72 frame, 1280x768) | 55x Fire, 48x Smoke terdeteksi, 10.9 FPS (CPU) |
| Real-Time (WebSocket) | 5 frame simulasi | Semua frame terdeteksi benar, sesi tersimpan ke DB |

Performa CPU: ~75-260ms per frame tergantung kompleksitas gambar.
Performa GPU (sesuai dokumentasi model asli): <15ms per frame (30-60 FPS).

## Kredit

- Model YOLO11: [sayedgamal99/Real-Time-Smoke-Fire-Detection-YOLO11](https://github.com/sayedgamal99/Real-Time-Smoke-Fire-Detection-YOLO11)
- Framework: [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
