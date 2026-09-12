"""
Verification + Human-in-the-Loop API endpoint.

Routes
------
GET  /tasks                            - List docs requiring human verification
GET  /records/{id}/verification        - Full verification details (fields + validation + duplicates)
PATCH /fields/{field_id}              - Correct a field value (human edit)
POST /records/{id}/approve            - Approve a finalized land record
POST /records/{id}/reject             - Reject an invalid / fraudulent record
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.models.extraction import ExtractedField
from app.models.audit import AuditLog
from app.models.correction import HumanCorrectionLog
from app.models.enums import DocumentStatus
from app.validation.engine import BhoomiSetuValidationEngine
from app.validation.duplicate_engine import DuplicateDetectionEngine

router = APIRouter()
logger = logging.getLogger(__name__)


class FieldPatchSchema(BaseModel):
    value: str
    reason: Optional[str] = "Verifier manual edit"


class VerificationTaskResponse(BaseModel):
    document_id: str
    original_filename: str
    status: str
    overall_confidence: float
    lowest_confidence_field: str
    lowest_confidence: float


@router.get("/tasks", response_model=List[VerificationTaskResponse])
def list_verification_tasks(db: Session = Depends(get_db)):
    """
    GET /api/v1/verification/tasks
    Returns all documents currently awaiting human verification,
    ordered by lowest confidence first (most urgent).
    """
    repo = DocumentRepository(db)
    docs = repo.get_all(limit=200)
    tasks = []
    for d in docs:
        if d.status not in (
            DocumentStatus.REQUIRES_VERIFICATION,
            DocumentStatus.NEEDS_VERIFICATION,
            DocumentStatus.VALIDATION_COMPLETE,
        ):
            continue
        fields = (
            db.query(ExtractedField)
            .filter(ExtractedField.document_id == d.document_id)
            .all()
        )
        lowest_field = min(fields, key=lambda f: f.confidence) if fields else None
        tasks.append(
            VerificationTaskResponse(
                document_id=d.document_id,
                original_filename=d.original_filename,
                status=d.status.value,
                overall_confidence=d.overall_confidence,
                lowest_confidence_field=lowest_field.field_name if lowest_field else "N/A",
                lowest_confidence=lowest_field.confidence if lowest_field else 0.0,
            )
        )
    # Sort by urgency (lowest confidence first)
    tasks.sort(key=lambda t: t.lowest_confidence)
    return tasks


@router.get("/records/{document_id}/verification")
def get_record_verification_details(document_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/verification/records/{id}/verification
    Returns full verification payload:
    - All extracted fields with source evidence
    - Validation rule results (run against actual extracted values)
    - Suspected duplicates (queried against approved DB records)
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document_id)
        .all()
    )
    fields_dict = {f.field_name: f.value for f in fields}

    # ── Validation ──────────────────────────────────────────────────────────
    validator = BhoomiSetuValidationEngine()
    validation_results = validator.validate_fields(fields_dict)

    # ── Duplicate Detection against approved records in DB ──────────────────
    # Query existing APPROVED documents (excluding the current one)
    from app.models.document import Document
    approved_docs = (
        db.query(Document)
        .filter(
            Document.status == DocumentStatus.APPROVED,
            Document.document_id != document_id,
        )
        .limit(500)
        .all()
    )

    existing_records = []
    for approved in approved_docs:
        approved_fields = (
            db.query(ExtractedField)
            .filter(ExtractedField.document_id == approved.document_id)
            .all()
        )
        rec = {"record_id": approved.document_id}
        for af in approved_fields:
            rec[af.field_name] = af.normalized_value or af.value
        existing_records.append(rec)

    duplicates = DuplicateDetectionEngine.evaluate(fields_dict, existing_records)

    return {
        "document_id": document_id,
        "filename": doc.original_filename,
        "file_url": f"/api/v1/documents/{document_id}/file",
        "mime_type": doc.mime_type,
        "status": doc.status.value,
        "overall_confidence": doc.overall_confidence,
        "fields": [
            {
                "field_id": f.field_id,
                "field_name": f.field_name,
                "value": f.value,
                "normalized_value": f.normalized_value,
                "confidence": f.confidence,
                "raw_text": f.raw_text,
                "source_bbox": f.source_bbox,
                "source_page": f.page_number,
                "extraction_method": f.extraction_method,
                "model_version": f.model_version,
                "is_verified": f.is_verified,
                "verified_at": f.verified_at.isoformat() if f.verified_at else None,
            }
            for f in fields
        ],
        "validation_results": [v.dict() for v in validation_results],
        "suspected_duplicates": [d.dict() for d in duplicates],
    }


@router.patch("/fields/{field_id}")
def update_field_value(
    field_id: str,
    payload: FieldPatchSchema,
    db: Session = Depends(get_db),
):
    """
    PATCH /api/v1/verification/fields/{field_id}
    Human verifier corrects a field value.
    Records both a correction log (for active learning) and an audit trail.
    """
    field = (
        db.query(ExtractedField)
        .filter(ExtractedField.field_id == field_id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    old_value = field.value
    new_value = payload.value.strip()

    if not new_value:
        raise HTTPException(status_code=400, detail="New value must not be empty")

    # Human correction feedback log (training data for future model improvement)
    correction = HumanCorrectionLog(
        field_id=field.field_id,
        document_id=field.document_id,
        field_name=field.field_name,
        ai_original_value=old_value,
        human_corrected_value=new_value,
        reason=payload.reason,
        source_bbox=field.source_bbox,
    )
    db.add(correction)

    # Immutable audit trail
    audit = AuditLog(
        entity_type="extracted_field",
        entity_id=field.field_id,
        action="VERIFIER_EDIT",
        changes={
            "field": field.field_name,
            "document_id": field.document_id,
            "old_value": old_value,
            "new_value": new_value,
            "reason": payload.reason,
        },
    )
    db.add(audit)

    # Update field
    field.value = new_value
    field.normalized_value = new_value
    field.confidence = 1.0   # Human-verified = 100% confidence
    field.is_verified = True
    field.verified_at = datetime.utcnow()

    db.commit()
    logger.info(f"Field {field_id} ({field.field_name}) corrected: '{old_value}' → '{new_value}'")

    return {
        "status": "SUCCESS",
        "field_id": field.field_id,
        "field_name": field.field_name,
        "old_value": old_value,
        "new_value": new_value,
        "is_verified": True,
    }


@router.post("/records/{document_id}/approve")
def approve_record(document_id: str, db: Session = Depends(get_db)):
    """
    POST /api/v1/verification/records/{id}/approve
    Supervisor approves a verified land record.
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    repo.update_status(document_id, DocumentStatus.APPROVED, 1.0)

    audit = AuditLog(
        entity_type="document",
        entity_id=document_id,
        action="SUPERVISOR_APPROVE",
        changes={"status": "APPROVED", "previous_status": doc.status.value},
    )
    db.add(audit)
    db.commit()

    logger.info(f"Document {document_id} approved by supervisor")
    return {
        "status": "SUCCESS",
        "message": "Document approved and recorded as master land record",
        "document_id": document_id,
    }


@router.post("/records/{document_id}/reject")
def reject_record(document_id: str, db: Session = Depends(get_db)):
    """
    POST /api/v1/verification/records/{id}/reject
    Supervisor rejects an invalid or fraudulent land record.
    """
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    repo.update_status(document_id, DocumentStatus.REJECTED if hasattr(DocumentStatus, "REJECTED") else DocumentStatus.FAILED, 0.0)

    audit = AuditLog(
        entity_type="document",
        entity_id=document_id,
        action="SUPERVISOR_REJECT",
        changes={"status": "REJECTED", "previous_status": doc.status.value},
    )
    db.add(audit)
    db.commit()

    logger.info(f"Document {document_id} rejected by supervisor")
    return {
        "status": "SUCCESS",
        "message": "Document rejected",
        "document_id": document_id,
    }
