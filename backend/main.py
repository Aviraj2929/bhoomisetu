import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.db.init_db import init_db
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)

app = FastAPI(
    title="BhoomiSetu Core Engine",
    description=(
        "Intelligent Land Record Digitization and Validation Platform. "
        "Processes scanned PDFs/images of Indian land records through an "
        "AI-powered OCR + extraction + validation pipeline."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Init on startup ───────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    init_db()
    logging.getLogger(__name__).info("BhoomiSetu backend started – database tables initialised.")

# ── API Routes ───────────────────────────────────────────────────────────────
# Single canonical prefix.  Do NOT double-mount the same router.
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "BhoomiSetu Core Engine",
        "version": "1.0.0",
        "ai_provider": settings.AI_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
