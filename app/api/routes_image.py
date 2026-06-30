"""
app/api/routes_image.py
------------------------
Endpoint FastAPI untuk deteksi api/asap pada gambar.

POST /api/detect/image
  - Menerima file gambar (multipart/form-data)
  - Menjalankan inferensi YOLO11
  - Menyimpan hasil ke database
  - Mengembalikan JSON hasil deteksi + URL gambar terdeteksi
"""

import time
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database import crud
from app.models.schemas import ImageDetectionResponse, ErrorResponse
from app.services.image_service import process_image
from app.utils.file_manager import save_upload_image, cleanup_file

router = APIRouter(prefix="/api/detect", tags=["Detection"])


@router.post(
    "/image",
    response_model=ImageDetectionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Deteksi api/asap pada gambar",
    description="Upload gambar JPG/PNG, dapatkan hasil deteksi beserta gambar beranotasi.",
)
async def detect_image(
    file: UploadFile = File(..., description="File gambar JPG atau PNG"),
    db: Session = Depends(get_db),
):
    input_path = None
    try:
        # 1. Simpan file upload
        input_path = await save_upload_image(file)

        # 2. Jalankan deteksi
        result = process_image(input_path)

        # 3. Simpan ke database
        session_data = {
            "mode":           "image",
            "filename":       file.filename,
            "output_path":    result["output_path"],
            "total_fire":     result["total_fire"],
            "total_smoke":    result["total_smoke"],
            "avg_confidence": result["avg_confidence"],
            "duration_sec":   result["duration_sec"],
        }
        db_session = crud.create_session(db, session_data)

        # 4. Simpan setiap deteksi ke database
        if result["detections"]:
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
                        "frame_number": 0,
                    }
                    for d in result["detections"]
                ],
            )

        # 5. Format response
        from app.models.schemas import DetectionItem, BoundingBox
        detections_out = [
            DetectionItem(
                class_name=d["class_name"],
                confidence=d["confidence"],
                bbox=BoundingBox(
                    x=d["bbox"]["x"],
                    y=d["bbox"]["y"],
                    w=d["bbox"]["w"],
                    h=d["bbox"]["h"],
                ),
            )
            for d in result["detections"]
        ]

        return ImageDetectionResponse(
            session_id=db_session.id,
            filename=file.filename,
            output_url=result["output_url"],
            detections=detections_out,
            total_fire=result["total_fire"],
            total_smoke=result["total_smoke"],
            avg_confidence=result["avg_confidence"],
            duration_sec=result["duration_sec"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Hapus file upload setelah diproses (output sudah disimpan)
        if input_path:
            cleanup_file(input_path)
