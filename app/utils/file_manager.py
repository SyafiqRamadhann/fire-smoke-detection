"""
app/utils/file_manager.py
--------------------------
Utilitas untuk manajemen file: validasi, simpan, hapus, generate URL.
"""

import uuid
import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings

BASE_DIR = Path(__file__).parent.parent.parent


def _allowed_extension(filename: str, allowed: str) -> bool:
    """Periksa apakah ekstensi file termasuk yang diizinkan."""
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext in [e.strip() for e in allowed.split(",")]


def generate_unique_filename(original: str) -> str:
    """
    Buat nama file unik dengan UUID agar tidak terjadi tabrakan.
    Contoh: 'fire.jpg' → 'a3f2b1c0-fire.jpg'
    """
    stem = Path(original).stem
    suffix = Path(original).suffix.lower()
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}-{stem}{suffix}"


async def save_upload_image(file: UploadFile) -> str:
    """
    Validasi dan simpan gambar yang diupload.
    Kembalikan path absolut file yang disimpan.
    Raise HTTPException jika validasi gagal.
    """
    # Validasi tipe file
    if not _allowed_extension(file.filename, settings.ALLOWED_IMAGE_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file tidak didukung. Gunakan: {settings.ALLOWED_IMAGE_TYPES}"
        )

    # Baca konten dan validasi ukuran
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File terlalu besar. Maksimum: {settings.MAX_IMAGE_SIZE_MB} MB"
        )

    # Simpan file
    unique_name = generate_unique_filename(file.filename)
    save_path = BASE_DIR / settings.UPLOAD_DIR / "images" / unique_name
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(content)

    return str(save_path)


async def save_upload_video(file: UploadFile) -> str:
    """
    Validasi dan simpan video yang diupload.
    Kembalikan path absolut file yang disimpan.
    """
    if not _allowed_extension(file.filename, settings.ALLOWED_VIDEO_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file tidak didukung. Gunakan: {settings.ALLOWED_VIDEO_TYPES}"
        )

    # Simpan langsung ke disk (streaming) karena video bisa besar
    unique_name = generate_unique_filename(file.filename)
    save_path = BASE_DIR / settings.UPLOAD_DIR / "videos" / unique_name
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        chunk_size = 1024 * 1024  # 1 MB per chunk
        while chunk := await file.read(chunk_size):
            size_written = save_path.stat().st_size / (1024 * 1024)
            if size_written > settings.MAX_VIDEO_SIZE_MB:
                save_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File terlalu besar. Maksimum: {settings.MAX_VIDEO_SIZE_MB} MB"
                )
            f.write(chunk)

    return str(save_path)


def get_output_image_path(original_filename: str) -> str:
    """Generate path output untuk gambar hasil deteksi."""
    unique_name = generate_unique_filename(original_filename)
    output_path = BASE_DIR / settings.OUTPUT_DIR / "images" / unique_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path)


def get_output_video_path(original_filename: str) -> str:
    """Generate path output untuk video hasil deteksi."""
    stem = Path(original_filename).stem
    unique_id = str(uuid.uuid4())[:8]
    unique_name = f"{unique_id}-{stem}.mp4"   # output selalu MP4
    output_path = BASE_DIR / settings.OUTPUT_DIR / "videos" / unique_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path)


def cleanup_file(file_path: str) -> None:
    """Hapus file jika ada (tidak raise error jika tidak ada)."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass


def path_to_url(file_path: str, base: str = "") -> str:
    """
    Konversi path absolut ke URL relatif untuk diakses browser.
    Contoh: '.../outputs/images/abc.jpg' → '/outputs/images/abc.jpg'
    """
    try:
        rel = Path(file_path).relative_to(BASE_DIR)
        return f"/{rel}"
    except ValueError:
        return file_path
