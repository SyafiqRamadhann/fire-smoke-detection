"""
app/services/camera_service.py
--------------------------------
Service untuk deteksi real-time dari webcam via WebSocket.

Protokol komunikasi:
  Browser → Server : frame gambar ter-encode sebagai base64 JPEG
  Server → Browser : JSON hasil deteksi + statistik per frame
"""

import cv2
import base64
import json
import time
import numpy as np
from typing import Dict, Any

from app.services.detection_service import detection_service
from app.utils.drawing import draw_detections, draw_fps_overlay


def decode_base64_frame(b64_data: str) -> np.ndarray:
    """
    Decode string base64 dari browser menjadi numpy array BGR.
    Format yang dikirim browser: data:image/jpeg;base64,<data>
    """
    # Hapus prefix data URL jika ada
    if "," in b64_data:
        b64_data = b64_data.split(",", 1)[1]

    # Decode base64 → bytes → numpy array → gambar
    img_bytes = base64.b64decode(b64_data)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    frame     = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Gagal decode frame dari base64")

    return frame


def encode_frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
    """
    Encode numpy array BGR menjadi base64 JPEG untuk dikirim ke browser.
    Quality 80 adalah kompromi baik antara ukuran dan kualitas.
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", frame, encode_params)
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


class CameraSession:
    """
    State untuk satu sesi WebSocket real-time.
    Mengelola FPS counter dan statistik per sesi.
    """

    def __init__(self):
        self.frame_count   = 0
        self.total_fire    = 0
        self.total_smoke   = 0
        self.fps_start     = time.perf_counter()
        self.fps_window    = 0
        self.current_fps   = 0.0
        self.is_active     = True

    def update_fps(self):
        """Perbarui hitung FPS setiap detik."""
        self.fps_window += 1
        elapsed = time.perf_counter() - self.fps_start
        if elapsed >= 1.0:
            self.current_fps = self.fps_window / elapsed
            self.fps_window  = 0
            self.fps_start   = time.perf_counter()

    def process_frame(self, b64_frame: str) -> Dict[str, Any]:
        """
        Proses satu frame dari WebSocket:
        1. Decode base64 → numpy
        2. Inferensi YOLO11
        3. Gambar anotasi
        4. Encode balik ke base64
        5. Kembalikan JSON response

        Return dict yang siap di-json.dumps() dan dikirim ke browser.
        """
        # Decode frame
        frame = decode_base64_frame(b64_frame)

        # Inferensi
        detections, inference_ms = detection_service.detect_with_timing(frame)

        # Statistik frame ini
        fire_count  = sum(1 for d in detections if d["class_name"] == "Fire")
        smoke_count = sum(1 for d in detections if d["class_name"] == "Smoke")
        self.total_fire  += fire_count
        self.total_smoke += smoke_count
        self.frame_count += 1

        # Update FPS
        self.update_fps()

        # Gambar anotasi pada frame
        annotated = draw_detections(frame, detections)
        annotated = draw_fps_overlay(
            annotated, self.current_fps,
            fire_count, smoke_count
        )

        # Encode frame hasil ke base64
        result_b64 = encode_frame_to_base64(annotated)

        # Siapkan response JSON
        response = {
            "status":        "detecting",
            "frame_number":  self.frame_count,
            "detections":    detections,
            "fire_count":    fire_count,
            "smoke_count":   smoke_count,
            "total_fire":    self.total_fire,
            "total_smoke":   self.total_smoke,
            "fps":           round(self.current_fps, 1),
            "inference_ms":  round(inference_ms, 1),
            "frame_base64":  result_b64,
        }

        return response

    def get_summary(self) -> Dict[str, Any]:
        """Kembalikan ringkasan seluruh sesi saat sesi berakhir."""
        return {
            "total_frames": self.frame_count,
            "total_fire":   self.total_fire,
            "total_smoke":  self.total_smoke,
            "avg_fps":      round(self.current_fps, 2),
        }
