"""
app/database/crud.py
--------------------
Fungsi-fungsi Create, Read, Update, Delete untuk database.
Semua fungsi menerima SQLAlchemy Session sebagai parameter pertama.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.models import DetectionSession, DetectionResult
from typing import List, Optional, Dict, Any


# ══════════════════════════════════════════════
#  DetectionSession
# ══════════════════════════════════════════════

def create_session(db: Session, data: Dict[str, Any]) -> DetectionSession:
    """Buat sesi deteksi baru."""
    session = DetectionSession(**data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> Optional[DetectionSession]:
    """Ambil satu sesi berdasarkan ID."""
    return db.query(DetectionSession).filter(
        DetectionSession.id == session_id
    ).first()


def get_sessions(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    mode: Optional[str] = None,
) -> List[DetectionSession]:
    """
    Ambil daftar sesi dengan pagination.
    Opsional filter berdasarkan mode ('image'|'video'|'realtime').
    """
    query = db.query(DetectionSession)
    if mode:
        query = query.filter(DetectionSession.mode == mode)
    return query.order_by(desc(DetectionSession.created_at)) \
                .offset(skip).limit(limit).all()


def update_session(
    db: Session,
    session_id: int,
    data: Dict[str, Any],
) -> Optional[DetectionSession]:
    """Update field-field pada sesi yang sudah ada."""
    session = get_session(db, session_id)
    if not session:
        return None
    for key, value in data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: int) -> bool:
    """Hapus sesi beserta semua result-nya (cascade)."""
    session = get_session(db, session_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


# ══════════════════════════════════════════════
#  DetectionResult
# ══════════════════════════════════════════════

def create_results_bulk(
    db: Session,
    session_id: int,
    results: List[Dict[str, Any]],
) -> List[DetectionResult]:
    """
    Simpan banyak hasil deteksi sekaligus (bulk insert).
    Lebih efisien daripada satu per satu untuk video panjang.
    """
    objects = [
        DetectionResult(session_id=session_id, **r)
        for r in results
    ]
    db.bulk_save_objects(objects)
    db.commit()
    return objects


def get_results_by_session(
    db: Session,
    session_id: int,
) -> List[DetectionResult]:
    """Ambil semua hasil deteksi untuk satu sesi."""
    return db.query(DetectionResult).filter(
        DetectionResult.session_id == session_id
    ).all()


# ══════════════════════════════════════════════
#  Statistik untuk Dashboard
# ══════════════════════════════════════════════

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """
    Hitung statistik global untuk ditampilkan di dashboard:
    - Total deteksi Fire dan Smoke
    - Rata-rata confidence
    - Rata-rata FPS
    - Sesi terakhir
    - Jumlah total sesi
    """
    total_sessions = db.query(func.count(DetectionSession.id)).scalar() or 0
    total_fire     = db.query(func.sum(DetectionSession.total_fire)).scalar() or 0
    total_smoke    = db.query(func.sum(DetectionSession.total_smoke)).scalar() or 0
    avg_conf       = db.query(func.avg(DetectionSession.avg_confidence)).scalar() or 0.0
    avg_fps        = db.query(func.avg(DetectionSession.fps)).scalar() or 0.0

    last_session = db.query(DetectionSession) \
                     .order_by(desc(DetectionSession.created_at)) \
                     .first()

    return {
        "total_sessions": total_sessions,
        "total_fire":     int(total_fire),
        "total_smoke":    int(total_smoke),
        "avg_confidence": round(float(avg_conf), 4),
        "avg_fps":        round(float(avg_fps), 2),
        "last_session":   last_session.to_dict() if last_session else None,
    }
