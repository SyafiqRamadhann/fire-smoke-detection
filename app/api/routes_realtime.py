"""
app/api/routes_realtime.py
---------------------------
WebSocket endpoint untuk deteksi api/asap secara real-time.

WS /ws/detect
  Browser kirim  : base64 JPEG frame setiap ~33ms (30 FPS)
  Server balas   : JSON { detections, fps, fire_count, smoke_count, frame_base64 }
  Browser kirim  : "stop" untuk mengakhiri sesi
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database import crud
from app.services.camera_service import CameraSession
from app.services.detection_service import detection_service

router = APIRouter(tags=["Real-Time"])


@router.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket handler untuk deteksi real-time.

    Protokol:
      1. Client kirim frame sebagai string base64 (data:image/jpeg;base64,...)
      2. Server proses → kirim JSON hasil
      3. Client kirim "stop" → server simpan ke DB dan tutup koneksi

    Error handling:
      - Jika frame tidak bisa di-decode, server kirim {"status":"error","message":"..."}
        tapi koneksi TETAP terbuka (tidak disconnect)
    """
    await websocket.accept()

    # Cek apakah model sudah siap
    if not detection_service.is_loaded:
        await websocket.send_json({
            "status":  "error",
            "message": "Model belum dimuat. Taruh file best.pt di folder weights/."
        })
        await websocket.close()
        return

    session = CameraSession()

    try:
        while session.is_active:
            # Terima pesan dari client
            data = await websocket.receive_text()

            # Client minta berhenti
            if data.strip().lower() == "stop":
                session.is_active = False
                break

            # Proses frame
            try:
                result = session.process_frame(data)
                await websocket.send_text(json.dumps(result))

            except ValueError as ve:
                # Frame rusak — beri tahu client tapi lanjut
                await websocket.send_json({
                    "status":  "error",
                    "message": f"Frame error: {str(ve)}",
                })
            except Exception as e:
                await websocket.send_json({
                    "status":  "error",
                    "message": f"Processing error: {str(e)}",
                })

    except WebSocketDisconnect:
        pass
    finally:
        # Simpan ringkasan sesi ke database jika ada frame yang diproses
        if session.frame_count > 0:
            summary = session.get_summary()
            crud.create_session(db, {
                "mode":        "realtime",
                "filename":    None,
                "output_path": None,
                "total_fire":  summary["total_fire"],
                "total_smoke": summary["total_smoke"],
                "fps":         summary["avg_fps"],
                "duration_sec": 0.0,
                "avg_confidence": 0.0,
            })
