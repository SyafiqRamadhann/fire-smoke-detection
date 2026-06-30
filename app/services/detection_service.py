"""
app/services/detection_service.py
-----------------------------------
Service inti: memuat model YOLO11 dan menjalankan inferensi.
Model dimuat SEKALI saat aplikasi start (singleton) agar tidak
terjadi overhead load model di setiap request.
"""

import time
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import settings, CLASS_NAMES

# Flag untuk mencegah import error saat model belum tersedia
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


class DetectionService:
    """
    Singleton service untuk inferensi YOLO11.

    Cara pakai:
        service = DetectionService()
        service.load_model()
        results = service.detect(frame)
    """

    _instance: Optional["DetectionService"] = None
    _model = None
    _is_loaded: bool = False
    _model_path: str = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self) -> bool:
        """
        Muat model YOLO11 dari path di config.
        Return True jika berhasil, False jika gagal.
        """
        if self._is_loaded:
            return True

        if not ULTRALYTICS_AVAILABLE:
            print("[DetectionService] ultralytics tidak terinstall!")
            return False

        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            print(f"[DetectionService] Model tidak ditemukan: {model_path}")
            print("  Silakan download model dari:")
            print("  https://github.com/sayedgamal99/Real-Time-Smoke-Fire-Detection-YOLO11")
            print("  Lalu simpan ke: weights/best.pt")
            return False

        try:
            print(f"[DetectionService] Memuat model dari {model_path}...")
            self._model = YOLO(str(model_path))
            self._model_path = str(model_path)
            self._is_loaded = True
            print("[DetectionService] Model berhasil dimuat!")
            return True
        except Exception as e:
            print(f"[DetectionService] Gagal memuat model: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_info(self) -> Dict[str, Any]:
        return {
            "loaded":     self._is_loaded,
            "model_path": self._model_path,
            "precision":  0.806,
            "recall":     0.717,
            "mAP50":      0.770,
            "classes":    CLASS_NAMES,
        }

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Jalankan inferensi pada satu frame/gambar.

        Parameter:
            frame : numpy array BGR (dari cv2.imread atau video frame)

        Return:
            List of dict, masing-masing:
            {
                "class_name":   "Fire" | "Smoke",
                "confidence":   float (0.0 - 1.0),
                "bbox": {"x": int, "y": int, "w": int, "h": int},
                "frame_number": 0
            }
        """
        if not self._is_loaded or self._model is None:
            return []

        try:
            results = self._model.predict(
                source=frame,
                conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                verbose=False,
            )

            detections = []
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_idx    = int(box.cls[0])
                    confidence = float(box.conf[0])
                    # Koordinat xyxy → xywh
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "class_name": CLASS_NAMES[cls_idx] if cls_idx < len(CLASS_NAMES) else "Unknown",
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x": int(x1),
                            "y": int(y1),
                            "w": int(x2 - x1),
                            "h": int(y2 - y1),
                        },
                        "frame_number": 0,
                    })

            return detections

        except Exception as e:
            print(f"[DetectionService] Error saat inferensi: {e}")
            return []

    def detect_with_timing(self, frame: np.ndarray) -> tuple[List[Dict], float]:
        """
        Seperti detect(), tapi juga kembalikan waktu inferensi (ms).
        Return: (detections, inference_ms)
        """
        t0 = time.perf_counter()
        detections = self.detect(frame)
        inference_ms = (time.perf_counter() - t0) * 1000
        return detections, inference_ms


# ── Singleton global — import ini di seluruh proyek ─────────────────
detection_service = DetectionService()
