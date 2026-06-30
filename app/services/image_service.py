"""
app/services/image_service.py
------------------------------
Service untuk memproses deteksi pada gambar statis.
Alur: baca gambar → inferensi → gambar anotasi → simpan output.
"""

import time
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any

from app.services.detection_service import detection_service
from app.utils.drawing import draw_detections
from app.utils.file_manager import get_output_image_path, path_to_url


def process_image(input_path: str) -> Dict[str, Any]:
    """
    Jalankan deteksi api/asap pada satu gambar.

    Parameter:
        input_path : path absolut gambar yang diupload

    Return:
        dict dengan keys:
        - detections   : list hasil deteksi
        - output_path  : path file gambar terdeteksi
        - output_url   : URL untuk diakses browser
        - total_fire   : jumlah Fire
        - total_smoke  : jumlah Smoke
        - avg_confidence
        - duration_sec
    """
    t_start = time.perf_counter()

    # ── Baca gambar ──────────────────────────────────────────────────
    frame = cv2.imread(input_path)
    if frame is None:
        raise ValueError(f"Tidak dapat membaca gambar: {input_path}")

    # ── Inferensi ────────────────────────────────────────────────────
    detections, inference_ms = detection_service.detect_with_timing(frame)

    # ── Hitung statistik ────────────────────────────────────────────
    total_fire  = sum(1 for d in detections if d["class_name"] == "Fire")
    total_smoke = sum(1 for d in detections if d["class_name"] == "Smoke")
    confidences = [d["confidence"] for d in detections]
    avg_conf    = sum(confidences) / len(confidences) if confidences else 0.0

    # ── Gambar anotasi ────────────────────────────────────────────────
    annotated = draw_detections(frame, detections)

    # ── Simpan output ────────────────────────────────────────────────
    original_name = Path(input_path).name
    output_path = get_output_image_path(original_name)
    cv2.imwrite(output_path, annotated)

    duration_sec = time.perf_counter() - t_start

    return {
        "detections":    detections,
        "output_path":   output_path,
        "output_url":    path_to_url(output_path),
        "total_fire":    total_fire,
        "total_smoke":   total_smoke,
        "avg_confidence": round(avg_conf, 4),
        "duration_sec":  round(duration_sec, 3),
        "inference_ms":  round(inference_ms, 2),
    }
