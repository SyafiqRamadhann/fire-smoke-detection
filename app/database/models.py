"""
app/database/models.py
----------------------
Definisi tabel database menggunakan SQLAlchemy ORM.

Tabel:
  - DetectionSession : satu sesi deteksi (1 gambar / 1 video / 1 session webcam)
  - DetectionResult  : setiap objek yang terdeteksi dalam satu sesi
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database.connection import Base


class DetectionSession(Base):
    """
    Merepresentasikan satu sesi deteksi.
    Satu sesi = satu upload gambar / satu upload video / satu sesi webcam.
    """
    __tablename__ = "detection_sessions"

    id           = Column(Integer, primary_key=True, index=True)
    mode         = Column(String(20), nullable=False)   # "image" | "video" | "realtime"
    filename     = Column(String(255), nullable=True)   # nama file original
    output_path  = Column(String(500), nullable=True)   # path file hasil
    duration_sec = Column(Float, default=0.0)           # durasi proses (detik)
    total_fire   = Column(Integer, default=0)           # jumlah total Fire terdeteksi
    total_smoke  = Column(Integer, default=0)           # jumlah total Smoke terdeteksi
    avg_confidence = Column(Float, default=0.0)         # rata-rata confidence
    fps          = Column(Float, default=0.0)           # FPS (untuk video/realtime)
    created_at   = Column(DateTime, default=datetime.utcnow)
    notes        = Column(Text, nullable=True)          # catatan tambahan

    # Relasi one-to-many ke DetectionResult
    results = relationship(
        "DetectionResult",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id":             self.id,
            "mode":           self.mode,
            "filename":       self.filename,
            "output_path":    self.output_path,
            "duration_sec":   self.duration_sec,
            "total_fire":     self.total_fire,
            "total_smoke":    self.total_smoke,
            "avg_confidence": round(self.avg_confidence, 4),
            "fps":            round(self.fps, 2),
            "created_at":     self.created_at.isoformat(),
            "notes":          self.notes,
        }


class DetectionResult(Base):
    """
    Setiap baris = satu objek yang terdeteksi dalam satu frame/gambar.
    Untuk gambar: frame_number = 0.
    Untuk video/realtime: frame_number = nomor frame.
    """
    __tablename__ = "detection_results"

    id           = Column(Integer, primary_key=True, index=True)
    session_id   = Column(Integer, ForeignKey("detection_sessions.id"), nullable=False)
    class_name   = Column(String(20), nullable=False)  # "Fire" | "Smoke"
    confidence   = Column(Float, nullable=False)
    bbox_x       = Column(Integer, default=0)           # koordinat bounding box
    bbox_y       = Column(Integer, default=0)
    bbox_w       = Column(Integer, default=0)
    bbox_h       = Column(Integer, default=0)
    frame_number = Column(Integer, default=0)

    # Relasi many-to-one ke DetectionSession
    session = relationship("DetectionSession", back_populates="results")

    def to_dict(self):
        return {
            "id":           self.id,
            "session_id":   self.session_id,
            "class_name":   self.class_name,
            "confidence":   round(self.confidence, 4),
            "bbox":         [self.bbox_x, self.bbox_y, self.bbox_w, self.bbox_h],
            "frame_number": self.frame_number,
        }
