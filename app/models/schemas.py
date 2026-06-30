"""
app/models/schemas.py
---------------------
Pydantic schemas untuk validasi request body dan serialisasi response.
Digunakan oleh FastAPI endpoint sebagai type hints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ══════════════════════════════════════════════
#  Detection — satu objek terdeteksi
# ══════════════════════════════════════════════

class BoundingBox(BaseModel):
    x: int = Field(..., description="Koordinat X pojok kiri atas")
    y: int = Field(..., description="Koordinat Y pojok kiri atas")
    w: int = Field(..., description="Lebar bounding box")
    h: int = Field(..., description="Tinggi bounding box")


class DetectionItem(BaseModel):
    class_name:   str        = Field(..., description="'Fire' atau 'Smoke'")
    confidence:   float      = Field(..., ge=0.0, le=1.0)
    bbox:         BoundingBox
    frame_number: int        = Field(default=0)


# ══════════════════════════════════════════════
#  Response untuk Image Detection
# ══════════════════════════════════════════════

class ImageDetectionResponse(BaseModel):
    session_id:    int
    filename:      str
    output_url:    str
    detections:    List[DetectionItem]
    total_fire:    int
    total_smoke:   int
    avg_confidence: float
    duration_sec:  float
    message:       str = "success"


# ══════════════════════════════════════════════
#  Response untuk Video Detection
# ══════════════════════════════════════════════

class VideoDetectionResponse(BaseModel):
    session_id:    int
    filename:      str
    output_url:    str
    total_frames:  int
    total_fire:    int
    total_smoke:   int
    avg_confidence: float
    fps:           float
    duration_sec:  float
    message:       str = "success"


# ══════════════════════════════════════════════
#  WebSocket — pesan real-time
# ══════════════════════════════════════════════

class WebSocketFrame(BaseModel):
    """Pesan yang dikirim server ke client setiap frame."""
    detections:   List[DetectionItem]
    total_fire:   int
    total_smoke:  int
    fps:          float
    frame_number: int
    status:       str = "detecting"   # "detecting" | "stopped"


# ══════════════════════════════════════════════
#  History & Dashboard
# ══════════════════════════════════════════════

class SessionSummary(BaseModel):
    id:             int
    mode:           str
    filename:       Optional[str]
    output_path:    Optional[str]
    duration_sec:   float
    total_fire:     int
    total_smoke:    int
    avg_confidence: float
    fps:            float
    created_at:     datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_sessions: int
    total_fire:     int
    total_smoke:    int
    avg_confidence: float
    avg_fps:        float
    last_session:   Optional[dict]


# ══════════════════════════════════════════════
#  Error Response
# ══════════════════════════════════════════════

class ErrorResponse(BaseModel):
    message: str
    detail:  Optional[str] = None
