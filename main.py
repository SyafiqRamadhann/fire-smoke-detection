"""
main.py
-------
Entry point aplikasi FastAPI Fire & Smoke Detection.

Cara menjalankan:
    python main.py
    atau
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Akses aplikasi di: http://localhost:8000
Dokumentasi API  : http://localhost:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from app.database.connection import init_db
from app.services.detection_service import detection_service

# ── Import semua router ──────────────────────────────────────────────
from app.api.routes_image    import router as image_router
from app.api.routes_video    import router as video_router
from app.api.routes_realtime import router as realtime_router
from app.api.routes_history  import router as history_router


# ── Lifecycle: startup & shutdown ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Dijalankan sekali saat aplikasi start (sebelum menerima request)
    dan sekali saat aplikasi shutdown.
    """
    print("=" * 55)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 55)

    # Inisialisasi database (buat tabel jika belum ada)
    print("[startup] Inisialisasi database...")
    init_db()
    print("[startup] Database siap.")

    # Muat model YOLO11
    print("[startup] Memuat model YOLO11...")
    loaded = detection_service.load_model()
    if loaded:
        print("[startup] Model siap digunakan.")
    else:
        print("[startup] PERINGATAN: Model tidak berhasil dimuat.")
        print("           Taruh file best.pt di folder weights/")
        print("           Download dari: github.com/sayedgamal99/Real-Time-Smoke-Fire-Detection-YOLO11")

    print(f"[startup] Server berjalan di http://{settings.HOST}:{settings.PORT}")
    print("=" * 55)

    yield  # Aplikasi berjalan di sini

    print("[shutdown] Aplikasi berhenti.")


# ── Inisialisasi FastAPI ─────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Aplikasi web deteksi api dan asap menggunakan YOLO11.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (izinkan semua saat development) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files & Templates ─────────────────────────────────────────
app.mount("/static",  StaticFiles(directory="static"),  name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

templates = Jinja2Templates(directory="templates")

# ── Daftarkan semua API router ────────────────────────────────────────
app.include_router(image_router)
app.include_router(video_router)
app.include_router(realtime_router)
app.include_router(history_router)


# ══════════════════════════════════════════════
#  Page Routes (mengembalikan HTML)
# ══════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"active_page": "dashboard"}
    )

@app.get("/image", response_class=HTMLResponse)
async def page_image(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="image_detection.html",
        context={"active_page": "image"}
    )

@app.get("/video", response_class=HTMLResponse)
async def page_video(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="video_detection.html",
        context={"active_page": "video"}
    )

@app.get("/live", response_class=HTMLResponse)
async def page_live(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="live_detection.html",
        context={"active_page": "live"}
    )

@app.get("/history", response_class=HTMLResponse)
async def page_history(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"active_page": "history"}
    )

@app.get("/about", response_class=HTMLResponse)
async def page_about(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={"active_page": "about"}
    )


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
