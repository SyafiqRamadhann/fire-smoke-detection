"""
app/database/connection.py
--------------------------
Konfigurasi koneksi database SQLite menggunakan SQLAlchemy.
Menyediakan engine, session factory, dan Base untuk ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# ── Engine ────────────────────────────────────────────────────────────
# connect_args check_same_thread=False diperlukan untuk SQLite
# agar bisa digunakan di multiple thread (FastAPI async)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,   # log SQL query saat DEBUG=True
)

# ── Session Factory ───────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Base Class untuk ORM Models ───────────────────────────────────────
Base = declarative_base()


def get_db():
    """
    Dependency injection untuk FastAPI endpoint.
    Memastikan session selalu ditutup setelah request selesai.

    Cara pakai di endpoint:
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Buat semua tabel di database berdasarkan ORM models.
    Dipanggil sekali saat aplikasi pertama kali dijalankan.
    """
    from app.database import models  # import di sini untuk hindari circular import
    Base.metadata.create_all(bind=engine)
