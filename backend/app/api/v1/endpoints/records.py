"""
Land Records endpoint – returns actual digitized records from the database.
No hardcoded sample records.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.document import Document
from app.models.extraction import ExtractedField
from app.models.enums import DocumentStatus

router = APIRouter()


class LandRecordResponse(BaseModel):
    record_id: str
    document_id: str
    original_filename: str
    status: str
    overall_confidence: float
    # Core extracted fields (may be None if extraction failed)
    owner_name: Optional[str] = None
    survey_number: Optional[str] = None
    khata_number: Optional[str] = None
    plot_area: Optional[str] = None
    area_unit: Optional[str] = None
    village: Optional[str] = None
    tehsil: Optional[str] = None
    district: Optional[str] = None


def _field_map(fields: list) -> dict:
    """Convert list of ExtractedField rows to {field_name: value} dict."""
    return {f.field_name: f.normalized_value or f.value for f in fields}


@router.get("/", response_model=List[LandRecordResponse])
def list_land_records(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/records/
    List all digitized land records.  Optionally filter by status.
    Only includes documents that have completed extraction (APPROVED, VERIFIED, REQUIRES_VERIFICATION).
    """
    query = db.query(Document)

    if status_filter:
        try:
            query = query.filter(Document.status == DocumentStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown status: {status_filter}")
    else:
        # Only show records that have gone through the pipeline
        query = query.filter(
            Document.status.in_([
                DocumentStatus.APPROVED,
                DocumentStatus.VERIFIED,
                DocumentStatus.REQUIRES_VERIFICATION,
                DocumentStatus.NEEDS_VERIFICATION,
                DocumentStatus.VALIDATION_COMPLETE,
                DocumentStatus.EXTRACTION_COMPLETE,
            ])
        )

    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for doc in docs:
        fm = _field_map(
            db.query(ExtractedField)
            .filter(ExtractedField.document_id == doc.document_id)
            .all()
        )
        results.append(
            LandRecordResponse(
                record_id=doc.document_id,
                document_id=doc.document_id,
                original_filename=doc.original_filename,
                status=doc.status.value,
                overall_confidence=doc.overall_confidence,
                owner_name=fm.get("owner_name"),
                survey_number=fm.get("survey_number"),
                khata_number=fm.get("khata_number"),
                plot_area=fm.get("plot_area"),
                area_unit=fm.get("area_unit"),
                village=fm.get("village"),
                tehsil=fm.get("tehsil"),
                district=fm.get("district"),
            )
        )
    return results


@router.get("/{document_id}", response_model=LandRecordResponse)
def get_land_record(document_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/records/{document_id}
    Get a single digitized land record with all extracted fields.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")

    fm = _field_map(
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document_id)
        .all()
    )

    return LandRecordResponse(
        record_id=doc.document_id,
        document_id=doc.document_id,
        original_filename=doc.original_filename,
        status=doc.status.value,
        overall_confidence=doc.overall_confidence,
        owner_name=fm.get("owner_name"),
        survey_number=fm.get("survey_number"),
        khata_number=fm.get("khata_number"),
        plot_area=fm.get("plot_area"),
        area_unit=fm.get("area_unit"),
        village=fm.get("village"),
        tehsil=fm.get("tehsil"),
        district=fm.get("district"),
    )
