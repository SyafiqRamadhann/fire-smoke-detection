"""
app/utils/drawing.py
---------------------
Fungsi utilitas untuk menggambar anotasi deteksi pada gambar/frame
menggunakan OpenCV. Dipakai oleh image_service dan video_service.
"""

import cv2
import numpy as np
from config import CLASS_COLORS, TEXT_COLOR


def draw_detections(frame: np.ndarray, detections: list) -> np.ndarray:
    """
    Gambar bounding box dan label pada frame/gambar.

    Parameter:
        frame      : numpy array BGR (hasil cv2.imread atau frame video)
        detections : list of dict dengan keys:
                     class_name, confidence, bbox (x,y,w,h)

    Return:
        frame dengan anotasi (numpy array BGR)
    """
    annotated = frame.copy()

    for det in detections:
        class_name = det.get("class_name", "Unknown")
        confidence = det.get("confidence", 0.0)
        bbox       = det.get("bbox", {})

        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        w = int(bbox.get("w", 0))
        h = int(bbox.get("h", 0))

        # Warna per kelas
        color = CLASS_COLORS.get(class_name, (0, 255, 0))

        # ── Bounding box ──────────────────────────────────────────────
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness=2)

        # ── Label background ──────────────────────────────────────────
        label = f"{class_name} {confidence:.0%}"
        (label_w, label_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        )
        label_bg_y1 = max(y - label_h - baseline - 4, 0)
        label_bg_y2 = max(y, label_h + baseline + 4)

        cv2.rectangle(
            annotated,
            (x, label_bg_y1),
            (x + label_w + 6, label_bg_y2),
            color,
            thickness=-1,   # filled
        )

        # ── Label teks ───────────────────────────────────────────────
        cv2.putText(
            annotated,
            label,
            (x + 3, max(y - baseline - 2, label_h + 2)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            TEXT_COLOR,
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    return annotated


def draw_fps_overlay(frame: np.ndarray, fps: float, count_fire: int, count_smoke: int) -> np.ndarray:
    """
    Gambar overlay info FPS dan jumlah objek di pojok kiri atas frame.
    Digunakan oleh mode real-time camera.
    """
    overlay = frame.copy()

    # Background semi-transparan
    bg_h, bg_w = 80, 220
    cv2.rectangle(overlay, (8, 8), (8 + bg_w, 8 + bg_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    texts = [
        (f"FPS: {fps:.1f}",        (12, 30),  (255, 255, 255)),
        (f"Fire:  {count_fire}",   (12, 52),  (0, 69, 255)),
        (f"Smoke: {count_smoke}",  (12, 74),  (180, 180, 180)),
    ]
    for text, pos, color in texts:
        cv2.putText(
            frame, text, pos,
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA
        )

    return frame
