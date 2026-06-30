"""
app/services/video_service.py
------------------------------
Service untuk memproses deteksi pada video frame-by-frame.
Output berupa video MP4 dengan anotasi bounding box.
"""

import time
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from app.services.detection_service import detection_service
from app.utils.drawing import draw_detections, draw_fps_overlay
from app.utils.file_manager import get_output_video_path, path_to_url


def process_video(
    input_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Jalankan deteksi api/asap pada video frame-by-frame.

    Parameter:
        input_path        : path absolut video yang diupload
        progress_callback : opsional fungsi callback(frame_current, frame_total)
                            untuk melaporkan progres

    Return:
        dict dengan hasil lengkap deteksi video
    """
    t_start = time.perf_counter()

    # ── Buka video ───────────────────────────────────────────────────
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Tidak dapat membuka video: {input_path}")

    # Properti video input
    original_fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_width    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # ── Siapkan output video ─────────────────────────────────────────
    original_name = Path(input_path).name
    output_path   = get_output_video_path(original_name)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(
        output_path, fourcc, original_fps,
        (frame_width, frame_height)
    )

    # ── Proses frame per frame ────────────────────────────────────────
    all_detections: list = []
    frame_number   = 0
    fire_frames    = 0
    smoke_frames   = 0
    fps_counter    = 0
    fps_start      = time.perf_counter()
    current_fps    = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Inferensi
        detections = detection_service.detect(frame)

        # Tambahkan nomor frame ke setiap deteksi
        for d in detections:
            d["frame_number"] = frame_number
        all_detections.extend(detections)

        # Hitung per-frame
        fire_in_frame  = sum(1 for d in detections if d["class_name"] == "Fire")
        smoke_in_frame = sum(1 for d in detections if d["class_name"] == "Smoke")
        if fire_in_frame > 0:
            fire_frames += fire_in_frame
        if smoke_in_frame > 0:
            smoke_frames += smoke_in_frame

        # Hitung FPS proses
        fps_counter += 1
        elapsed = time.perf_counter() - fps_start
        if elapsed >= 1.0:
            current_fps = fps_counter / elapsed
            fps_counter = 0
            fps_start   = time.perf_counter()

        # Gambar anotasi
        annotated = draw_detections(frame, detections)
        annotated = draw_fps_overlay(
            annotated, current_fps,
            fire_in_frame, smoke_in_frame
        )
        out.write(annotated)

        frame_number += 1
        if progress_callback and total_frames > 0:
            progress_callback(frame_number, total_frames)

    cap.release()
    out.release()

    # ── Statistik akhir ───────────────────────────────────────────────
    confidences  = [d["confidence"] for d in all_detections]
    avg_conf     = sum(confidences) / len(confidences) if confidences else 0.0
    duration_sec = time.perf_counter() - t_start
    avg_fps      = frame_number / duration_sec if duration_sec > 0 else 0.0

    return {
        "output_path":    output_path,
        "output_url":     path_to_url(output_path),
        "total_frames":   frame_number,
        "total_fire":     fire_frames,
        "total_smoke":    smoke_frames,
        "avg_confidence": round(avg_conf, 4),
        "fps":            round(avg_fps, 2),
        "duration_sec":   round(duration_sec, 3),
        "detections":     all_detections,
    }
