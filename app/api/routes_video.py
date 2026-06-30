"""
app/api/routes_video.py
------------------------
Endpoint FastAPI untuk deteksi api/asap pada video.

POST /api/detect/video
  - Menerima file video (MP4/AVI)
  - Memproses setiap frame dengan YOLO11
  - Mengembalikan video hasil + statistik
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database import crud
from app.models.schemas import VideoDetectionResponse, ErrorResponse
from app.services.video_service import process_video
from app.utils.file_manager import save_upload_video, cleanup_file

router = APIRouter(prefix="/api/detect", tags=["Detection"])


@router.post(
    "/video",
    response_model=VideoDetectionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Deteksi api/asap pada video",
    description="Upload video MP4/AVI, proses frame-by-frame, dapatkan video hasil.",
)
async def detect_video(
    file: UploadFile = File(..., description="File video MP4 atau AVI"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    input_path = None
    try:
        # 1. Simpan file upload
        input_path = await save_upload_video(file)

        # 2. Jalankan deteksi (proses sync, bisa lama untuk video panjang)
        result = process_video(input_path)

        # 3. Simpan ke database
        session_data = {
            "mode":           "video",
            "filename":       file.filename,
            "output_path":    result["output_path"],
            "total_fire":     result["total_fire"],
            "total_smoke":    result["total_smoke"],
            "avg_confidence": result["avg_confidence"],
            "fps":            result["fps"],
            "duration_sec":   result["duration_sec"],
        }
        db_session = crud.create_session(db, session_data)

        # 4. Simpan sampel deteksi ke database (maksimal 500 baris per video)
        sample = result["detections"][:500]
        if sample:
            crud.create_results_bulk(
                db, db_session.id,
                [
                    {
                        "class_name":   d["class_name"],
                        "confidence":   d["confidence"],
                        "bbox_x":       d["bbox"]["x"],
                        "bbox_y":       d["bbox"]["y"],
                        "bbox_w":       d["bbox"]["w"],
                        "bbox_h":       d["bbox"]["h"],
                        "frame_number": d["frame_number"],
                    }
                    for d in sample
                ],
            )

        # 5. Hapus file upload di background (hemat disk)
        background_tasks.add_task(cleanup_file, input_path)
        input_path = None  # jangan hapus lagi di finally

        return VideoDetectionResponse(
            session_id=db_session.id,
            filename=file.filename,
            output_url=result["output_url"],
            total_frames=result["total_frames"],
            total_fire=result["total_fire"],
            total_smoke=result["total_smoke"],
            avg_confidence=result["avg_confidence"],
            fps=result["fps"],
            duration_sec=result["duration_sec"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path:
            cleanup_file(input_path)
