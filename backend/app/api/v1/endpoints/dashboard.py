"""
Real-time Dashboard analytics – computed from actual database records.
No hardcoded numbers.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.document import Document
from app.models.extraction import ExtractedField
from app.models.enums import DocumentStatus

router = APIRouter()


@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    GET /api/v1/analytics/metrics
    Returns live stats computed from PostgreSQL / SQLite.
    """
    total = db.query(func.count(Document.document_id)).scalar() or 0
    approved = db.query(func.count(Document.document_id)).filter(
        Document.status == DocumentStatus.APPROVED
    ).scalar() or 0

    needs_verification = db.query(func.count(Document.document_id)).filter(
        Document.status.in_([
            DocumentStatus.REQUIRES_VERIFICATION,
            DocumentStatus.NEEDS_VERIFICATION,
        ])
    ).scalar() or 0

    verified = db.query(func.count(Document.document_id)).filter(
        Document.status == DocumentStatus.VERIFIED
    ).scalar() or 0

    failed = db.query(func.count(Document.document_id)).filter(
        Document.status == DocumentStatus.FAILED
    ).scalar() or 0

    processing = db.query(func.count(Document.document_id)).filter(
        Document.status.in_([
            DocumentStatus.QUEUED,
            DocumentStatus.PROCESSING,
            DocumentStatus.OCR_PROCESSING,
            DocumentStatus.EXTRACTION_PROCESSING,
            DocumentStatus.VALIDATING,
        ])
    ).scalar() or 0

    # Average confidence across all extracted fields
    avg_conf_row = db.query(func.avg(ExtractedField.confidence)).scalar()
    avg_field_confidence = round(float(avg_conf_row), 3) if avg_conf_row else 0.0

    # Average confidence of approved documents
    avg_approved_conf_row = db.query(func.avg(Document.overall_confidence)).filter(
        Document.status == DocumentStatus.APPROVED
    ).scalar()
    avg_approved_conf = round(float(avg_approved_conf_row), 3) if avg_approved_conf_row else 0.0

    # Auto-approval rate (approved out of processed, excluding still-uploading/failed)
    processed = total - (db.query(func.count(Document.document_id)).filter(
        Document.status == DocumentStatus.UPLOADED
    ).scalar() or 0)
    auto_approval_rate = f"{round((approved / max(processed, 1)) * 100, 1)}%" if processed else "0%"

    return {
        "total_documents": total,
        "auto_approved": approved,
        "needs_verification": needs_verification,
        "human_verified": verified,
        "failed": failed,
        "currently_processing": processing,
        "auto_approval_rate": auto_approval_rate,
        "avg_processing_time_sec": None,   # Not tracked yet; placeholder
        "avg_field_confidence": avg_field_confidence,
        "avg_approved_confidence": avg_approved_conf,
        "action_required": {
            "pending_verifications": needs_verification,
            "validation_failures": failed,
            "duplicate_suspects": 0,         # Populated by duplicate engine in future
        },
    }
