"""
app/api/routes_history.py
--------------------------
Endpoint untuk riwayat deteksi dan statistik dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional, List

from app.database.connection import get_db
from app.database import crud
from app.models.schemas import DashboardStats, ErrorResponse

router = APIRouter(prefix="/api", tags=["History & Stats"])


@router.get("/stats", response_model=DashboardStats, summary="Statistik dashboard")
def get_stats(db: Session = Depends(get_db)):
    """Kembalikan statistik global untuk ditampilkan di dashboard."""
    return crud.get_dashboard_stats(db)


@router.get("/history", summary="Daftar riwayat deteksi")
def get_history(
    skip:  int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    mode:  Optional[str] = Query(None, description="Filter: image | video | realtime"),
    db:    Session = Depends(get_db),
):
    """Kembalikan daftar sesi deteksi dengan pagination."""
    sessions = crud.get_sessions(db, skip=skip, limit=limit, mode=mode)
    return [s.to_dict() for s in sessions]


@router.get("/history/{session_id}", summary="Detail satu sesi")
def get_session_detail(session_id: int, db: Session = Depends(get_db)):
    """Kembalikan detail satu sesi beserta semua hasil deteksinya."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")

    results = crud.get_results_by_session(db, session_id)
    data    = session.to_dict()
    data["results"] = [r.to_dict() for r in results]
    return data


@router.delete(
    "/history/{session_id}",
    summary="Hapus satu sesi",
    responses={404: {"model": ErrorResponse}},
)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Hapus sesi beserta semua hasil deteksi dan file output-nya."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")

    # Hapus file output jika ada
    if session.output_path and Path(session.output_path).exists():
        Path(session.output_path).unlink(missing_ok=True)

    crud.delete_session(db, session_id)
    return {"message": "Sesi berhasil dihapus", "session_id": session_id}


@router.get("/download/{media_type}/{filename}", summary="Download file hasil deteksi")
def download_file(media_type: str, filename: str):
    """
    Download file hasil deteksi.
    media_type: 'images' atau 'videos'
    """
    if media_type not in ("images", "videos"):
        raise HTTPException(status_code=400, detail="media_type harus 'images' atau 'videos'")

    base = Path(__file__).parent.parent.parent
    file_path = base / "outputs" / media_type / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="image/jpeg" if media_type == "images" else "video/mp4",
    )


@router.get("/model/info", summary="Info model yang digunakan")
def get_model_info():
    """Kembalikan informasi model YOLO11 yang sedang digunakan."""
    from app.services.detection_service import detection_service
    return detection_service.model_info
