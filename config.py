"""
config.py
---------
Konfigurasi global aplikasi menggunakan pydantic-settings.
Semua nilai dibaca dari file .env secara otomatis.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ── Informasi Aplikasi ──────────────────────────────────────────
    APP_NAME: str = "Fire & Smoke Detection"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"

    # ── Server ──────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Model YOLO11 ─────────────────────────────────────────────────
    MODEL_PATH: str = "weights/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.35
    IOU_THRESHOLD: float = 0.10

    # ── Upload & Output ──────────────────────────────────────────────
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_VIDEO_SIZE_MB: int = 500
    ALLOWED_IMAGE_TYPES: str = "jpg,jpeg,png"
    ALLOWED_VIDEO_TYPES: str = "mp4,avi,mov"
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    DATABASE_DIR: str = "database"

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///database/detections.db"

    # ── WebSocket / Real-Time ────────────────────────────────────────
    WS_MAX_FRAME_SIZE: int = 5242880  # 5 MB
    CAMERA_FPS_LIMIT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance — import dari sini di seluruh proyek
settings = Settings()

# ── Pastikan semua direktori ada ─────────────────────────────────────
BASE_DIR = Path(__file__).parent

REQUIRED_DIRS = [
    BASE_DIR / settings.UPLOAD_DIR / "images",
    BASE_DIR / settings.UPLOAD_DIR / "videos",
    BASE_DIR / settings.OUTPUT_DIR / "images",
    BASE_DIR / settings.OUTPUT_DIR / "videos",
    BASE_DIR / settings.DATABASE_DIR,
    BASE_DIR / "weights",
]

for _dir in REQUIRED_DIRS:
    _dir.mkdir(parents=True, exist_ok=True)

# ── Konstanta yang sering dipakai ────────────────────────────────────
CLASS_NAMES = ["Fire", "Smoke"]

# Warna bounding box per kelas (BGR untuk OpenCV)
CLASS_COLORS = {
    "Fire":  (0,   69,  255),   # merah-oranye
    "Smoke": (128, 128, 128),   # abu-abu
}

# Warna label teks (BGR)
TEXT_COLOR = (255, 255, 255)   # putih
