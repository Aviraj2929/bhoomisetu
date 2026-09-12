"""
DocumentProcessingService – orchestrates the end-to-end pipeline.

Workflow:
  UPLOADED → QUEUED → PROCESSING → OCR_PROCESSING → OCR_COMPLETE
  → EXTRACTION_PROCESSING → EXTRACTION_COMPLETE → VALIDATING
  → VALIDATION_COMPLETE → REQUIRES_VERIFICATION | APPROVED | FAILED
"""
import logging
from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.preprocessing_service import OpenCVPreprocessor
from app.ai.factory import get_ocr_provider
from app.models.extraction import ExtractedField
from app.models.enums import DocumentStatus
from app.validation.engine import BhoomiSetuValidationEngine
from app.validation.duplicate_engine import DuplicateDetectionEngine

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)

    def _set_status(self, document_id: str, status: DocumentStatus, confidence: float = 0.0):
        """Update document status without resetting existing confidence unless provided."""
        doc = self.repo.get_by_id(document_id)
        if doc:
            doc.status = status
            # Only overwrite confidence if a non-zero value is given
            if confidence > 0.0:
                doc.overall_confidence = confidence
            self.db.commit()

    def process_document(self, document_id: str):
        """
        Run the full processing pipeline for a document.
        Transitions the document through all pipeline states.
        Catches and records any errors, setting status = FAILED.
        """
        doc = self.repo.get_by_id(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found – aborting pipeline.")
            return None

        logger.info(f"[Pipeline] Starting for document {document_id} ({doc.original_filename})")

        try:
            # ── Step 1: Queue + start ────────────────────────────────────────
            self._set_status(document_id, DocumentStatus.QUEUED)
            self._set_status(document_id, DocumentStatus.PROCESSING)

            # ── Step 2: OpenCV preprocessing ─────────────────────────────────
            prep_result = OpenCVPreprocessor.process(doc.storage_path)
            logger.info(f"[Pipeline] Preprocessing: {prep_result}")

            # ── Step 3: OCR ──────────────────────────────────────────────────
            self._set_status(document_id, DocumentStatus.OCR_PROCESSING)
            ocr_provider = get_ocr_provider()
            logger.info(f"[Pipeline] Running OCR via {ocr_provider.__class__.__name__}")
            ocr_payload = ocr_provider.process_image(doc.storage_path)
            self._set_status(document_id, DocumentStatus.OCR_COMPLETE)
            logger.info(
                f"[Pipeline] OCR complete – detected language: {ocr_payload.detected_language}, "
                f"text length: {len(ocr_payload.full_text)} chars, "
                f"tokens: {len(ocr_payload.tokens)}, "
                f"extracted fields: {len(ocr_payload.extracted_fields)}"
            )

            # ── Step 4: Persist extracted fields ─────────────────────────────
            self._set_status(document_id, DocumentStatus.EXTRACTION_PROCESSING)

            # Clear old extraction results for idempotency (e.g. on retry)
            self.db.query(ExtractedField).filter(
                ExtractedField.document_id == document_id
            ).delete()
            self.db.flush()

            total_conf = 0.0
            fields_dict = {}

            for f_data in ocr_payload.extracted_fields:
                if not f_data.value:
                    continue  # Skip fields with no value extracted

                field = ExtractedField(
                    document_id=document_id,
                    page_number=f_data.source_page,
                    field_name=f_data.field_name,
                    value=f_data.value,
                    normalized_value=f_data.normalized_value,
                    confidence=f_data.confidence,
                    raw_text=f_data.raw_text,
                    source_bbox=f_data.bounding_box,
                    extraction_method=f_data.extraction_method,
                    model_version=f_data.model_version,
                )
                self.db.add(field)
                total_conf += f_data.confidence
                fields_dict[f_data.field_name] = f_data.value

            num_fields = len(fields_dict)
            avg_conf = total_conf / max(num_fields, 1)

            self._set_status(document_id, DocumentStatus.EXTRACTION_COMPLETE)
            logger.info(
                f"[Pipeline] Extracted {num_fields} fields, avg confidence: {avg_conf:.3f}"
            )

            # ── Step 5: Validation ───────────────────────────────────────────
            self._set_status(document_id, DocumentStatus.VALIDATING)
            validator = BhoomiSetuValidationEngine()
            validation_results = validator.validate_fields(fields_dict)
            has_failures = any(v.status == "FAIL" for v in validation_results)

            failed_rules = [v.rule_id for v in validation_results if v.status == "FAIL"]
            warn_rules = [v.rule_id for v in validation_results if v.status == "WARNING"]
            logger.info(
                f"[Pipeline] Validation complete – FAIL rules: {failed_rules}, "
                f"WARNING rules: {warn_rules}"
            )

            self._set_status(document_id, DocumentStatus.VALIDATION_COMPLETE)

            # ── Step 6: Route to final status ────────────────────────────────
            # Require human verification if:
            #   - Any extraction confidence < 0.75
            #   - Average confidence < 0.85
            #   - Any validation FAIL rule triggered
            #   - No fields extracted at all (something is very wrong)
            low_confidence_field = any(
                f_data.confidence < 0.75 for f_data in ocr_payload.extracted_fields
                if f_data.value
            )

            if num_fields == 0 or avg_conf < 0.85 or has_failures or low_confidence_field:
                final_status = DocumentStatus.REQUIRES_VERIFICATION
                reason = (
                    f"num_fields={num_fields}, avg_conf={avg_conf:.2f}, "
                    f"failures={has_failures}, low_conf_field={low_confidence_field}"
                )
                logger.info(f"[Pipeline] → REQUIRES_VERIFICATION ({reason})")
            else:
                final_status = DocumentStatus.APPROVED
                logger.info(f"[Pipeline] → APPROVED (high confidence, no validation failures)")

            # Persist confidence before final commit
            doc = self.repo.get_by_id(document_id)
            if doc:
                doc.status = final_status
                doc.overall_confidence = round(avg_conf, 4)
                self.db.commit()

            logger.info(f"[Pipeline] Completed for {document_id} → {final_status.value}")
            return doc

        except Exception as e:
            logger.error(
                f"[Pipeline] FAILED for document {document_id}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            try:
                self._set_status(document_id, DocumentStatus.FAILED)
                self.db.commit()
            except Exception as db_err:
                logger.error(f"[Pipeline] Could not persist FAILED status: {db_err}")
            raise
