"""
Documents API endpoint.

Key behaviours
--------------
- POST /          : Upload a file, store it, trigger async processing pipeline.
- GET  /          : List all uploaded documents from DB.
- GET  /{id}      : Get a single document record.
- GET  /{id}/status : Poll the processing status.
- POST /{id}/process : Manually re-trigger the pipeline (e.g., after a failure).
- GET  /{id}/fields  : Return extracted fields from DB (never re-runs OCR on demand).
- DELETE /{id}    : Remove a document and its extracted fields.
"""
import os
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentProcessingService
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.field import FieldResponse
from app.models.extraction import ExtractedField
from app.models.enums import DocumentStatus
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
    "image/webp",
    "application/octet-stream",   # Some browsers send this for PDFs
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024   # 50 MB


def _run_pipeline(doc_id: str):
    """Run the processing pipeline in a background thread with its own DB session."""
    db_session = next(get_db())
    try:
        service = DocumentProcessingService(db_session)
        service.process_document(doc_id)
    except Exception as e:
        logger.error(f"Pipeline background task error for {doc_id}: {e}", exc_info=True)
    finally:
        db_session.close()


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/documents/
    Upload a scanned land-record PDF or image.
    Stores the file and asynchronously triggers the OCR + extraction pipeline.
    """
    # ── Validate MIME type ──────────────────────────────────────────────────
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: '{content_type}'. "
                   f"Accepted: PDF, PNG, JPEG, TIFF, BMP, WebP",
        )

    # ── Read & validate size ────────────────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes) // (1024*1024)} MB). Max 50 MB.",
        )

    # ── Deduplicate by SHA-256 ──────────────────────────────────────────────
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    repo = DocumentRepository(db)
    existing = db.query(__import__("app.models.document", fromlist=["Document"]).Document).filter_by(
        file_hash_sha256=file_hash
    ).first()
    if existing:
        logger.info(f"Duplicate upload detected for hash {file_hash}, returning existing record.")
        return existing

    # ── Persist file to storage ─────────────────────────────────────────────
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    safe_name = file.filename.replace("/", "_").replace("\\", "_") if file.filename else "upload"
    file_path = os.path.join(settings.STORAGE_DIR, f"{file_hash[:16]}_{safe_name}")
    with open(file_path, "wb") as fp:
        fp.write(file_bytes)

    logger.info(f"Stored uploaded file at '{file_path}' ({len(file_bytes)} bytes)")

    # ── Create DB record ────────────────────────────────────────────────────
    doc = repo.create(
        filename=file.filename or "unknown",
        size=len(file_bytes),
        mime_type=content_type,
        file_hash=file_hash,
        storage_path=file_path,
    )

    # ── Kick off async processing ───────────────────────────────────────────
    background_tasks.add_task(_run_pipeline, doc.document_id)
    logger.info(f"Processing pipeline dispatched for document {doc.document_id}")

    return doc


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """GET /api/v1/documents/  – list all uploaded documents (newest first)."""
    repo = DocumentRepository(db)
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/documents/{id}  – get a single document record."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """GET /api/v1/documents/{id}/status  – poll processing status."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(
        document_id=doc.document_id,
        status=doc.status,
        overall_confidence=doc.overall_confidence,
        message=f"Processing status: {doc.status.value}",
    )


@router.post("/{document_id}/process", response_model=DocumentStatusResponse)
def trigger_process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/documents/{id}/process
    Manually re-trigger the processing pipeline (e.g., after a FAILED status).
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    background_tasks.add_task(_run_pipeline, document_id)

    return DocumentStatusResponse(
        document_id=doc.document_id,
        status=doc.status,
        overall_confidence=doc.overall_confidence,
        message="Processing pipeline re-dispatched",
    )


@router.get("/{document_id}/fields", response_model=List[FieldResponse])
def get_document_fields(document_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/documents/{id}/fields
    Return the extracted fields stored in the database.

    Returns 404 if the document doesn't exist.
    Returns 202 (via a descriptive empty list) if extraction hasn't finished yet.
    Never re-runs OCR on demand here – that is done by the background pipeline.
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document_id)
        .order_by(ExtractedField.confidence.asc())
        .all()
    )

    # If the pipeline hasn't finished yet, return an empty list (not a mock)
    return fields


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    DELETE /api/v1/documents/{id}
    Remove document and all extracted fields.
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.query(ExtractedField).filter(ExtractedField.document_id == document_id).delete()
    db.delete(doc)
    db.commit()
    logger.info(f"Deleted document {document_id} and associated fields")
