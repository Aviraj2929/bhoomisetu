"""
Sarvam AI Document Intelligence Provider (Official SDK).

Uses the `sarvamai` Python SDK to call Sarvam Vision 1.5 via the Doc AI API.

Two-stage pipeline per document:
  1. digitise()  → full OCR text + layout (markdown output)
  2. extract()   → schema-based structured field extraction (JSON)

Both calls use the official SDK (not raw HTTP), which handles auth, retries,
and serialization correctly.

Base URL: https://api.sarvam.ai  (SDK default)
Auth:     api-subscription-key header (passed via api_subscription_key param)
"""
import json
import os
import time
import logging
import mimetypes
from typing import Optional, List

from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError

from app.ai.ocr_interface import (
    OCRProvider,
    OCRResponsePayload,
    OCRToken,
    FieldExtractionResult,
)
from app.ai.extraction import LandRecordExtractionParser

logger = logging.getLogger(__name__)

# ── Poll settings ────────────────────────────────────────────────────────────
POLL_INTERVAL_SECS = 3
MAX_WAIT_SECS = 120   # 2 minutes max
TERMINAL_STATES = {"completed", "partially_completed", "failed", "rejected"}

# ── Land-record extraction schema for Sarvam Vision 1.5 ─────────────────────
# Using "extract" mode: we define exactly the fields we want and the model
# returns them as structured JSON. This is far more accurate than our regex
# parser on unknown documents.
LAND_RECORD_SCHEMA = {
    "type": "object",
    "properties": {
        "survey_number": {
            "type": "string",
            "description": (
                "Khasra number or survey number of the land plot. "
                "Usually a number or number/sub-number like '123' or '123/4'. "
                "Look for labels: खसरा नं, खसरा संख्या, Survey No, Khasra No."
            ),
        },
        "khata_number": {
            "type": "string",
            "description": (
                "Khata number or account number of the land owner. "
                "Look for labels: खाता संख्या, खाता नं, खेवट नं, Khata No, Account No."
            ),
        },
        "owner_name": {
            "type": "string",
            "description": (
                "Full name of the land owner or khatedar. "
                "Look for labels: खातेदार, मालिक, काश्तकार, स्वामी, Owner Name, Khatedar."
            ),
        },
        "plot_area": {
            "type": "string",
            "description": (
                "Numeric area value of the land plot (digits only, no unit). "
                "Look for labels: क्षेत्रफल, रकबा, Area. Example values: '1.250', '0.500', '2.75'."
            ),
        },
        "area_unit": {
            "type": "string",
            "description": (
                "Unit of area measurement. Common values: Hectare (हेक्टेयर), Acre (एकड़), "
                "Bigha (बीघा), Guntha (गुंठा). Normalize to English name."
            ),
            "enum": ["Hectare", "Acre", "Bigha", "Guntha", "Cent", "Square Meter", "Unknown"],
        },
        "village": {
            "type": "string",
            "description": (
                "Village or Gram name where the land is located. "
                "Look for labels: ग्राम, मौजा, गांव, Village."
            ),
        },
        "tehsil": {
            "type": "string",
            "description": (
                "Tehsil or Taluka name. "
                "Look for labels: तहसील, तालुका, Tehsil, Taluka, Mandal."
            ),
        },
        "district": {
            "type": "string",
            "description": (
                "District name. "
                "Look for labels: जिला, जनपद, District."
            ),
        },
        "state": {
            "type": "string",
            "description": "Indian state name (e.g. Madhya Pradesh, Maharashtra, Rajasthan).",
        },
        "land_type": {
            "type": "string",
            "description": (
                "Type or classification of land (e.g. Agricultural, Irrigated, Non-irrigated, Forest). "
                "Look for labels: भूमि प्रकार, भूमि वर्गीकरण, Land Type."
            ),
        },
        "document_type": {
            "type": "string",
            "description": (
                "Type of this land record document. Examples: Khasra, Khatauni, 7/12 Extract, "
                "Pahani, Jamabandi, RoR (Record of Rights), Patta."
            ),
        },
        "year": {
            "type": "string",
            "description": "Year or agricultural year (Kharif/Rabi year) printed on the document.",
        },
    },
}


def _poll_until_done(client: SarvamAI, job_id: str) -> str:
    """Poll get_status until terminal state. Returns final status string."""
    waited = 0
    while waited < MAX_WAIT_SECS:
        status_resp = client.doc_ai.get_status(job_id=job_id)
        status = (status_resp.status or "").lower()
        pages_done = getattr(status_resp.usage, "pages_processed", "?")
        pages_total = getattr(status_resp.usage, "pages_total", "?")
        logger.info(
            f"[Sarvam DocAI] job={job_id} status={status} pages={pages_done}/{pages_total}"
        )
        if status in TERMINAL_STATES:
            return status
        time.sleep(POLL_INTERVAL_SECS)
        waited += POLL_INTERVAL_SECS

    raise TimeoutError(
        f"Sarvam DocAI job {job_id} did not complete within {MAX_WAIT_SECS}s."
    )


class SarvamOCRProvider(OCRProvider):
    """
    Real Sarvam AI Document Intelligence provider using the official SDK.

    Two-stage pipeline:
      Stage 1 – digitise(): full-document OCR → markdown text (full_text)
      Stage 2 – extract():  schema-based extraction → structured land-record fields

    Stage 1 gives us the raw OCR text for the `full_text` field and token list.
    Stage 2 gives us precise field values returned directly by Sarvam Vision 1.5.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "SarvamOCRProvider: SARVAM_API_KEY is missing. "
                "Set it in your .env file to use real Sarvam AI OCR."
            )
        self.api_key = api_key
        self.client = SarvamAI(api_subscription_key=api_key)
        logger.info("[Sarvam] SDK client initialised (base: api.sarvam.ai)")

    def _detect_language(self, path: str) -> str:
        """Heuristic: return the best language hint based on file name or default hi-IN."""
        name = os.path.basename(path).lower()
        # Future: can be expanded with an explicit language param
        return "hi-IN"

    def _get_mime(self, path: str) -> str:
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            with open(path, "rb") as f:
                header = f.read(4)
            mime = "application/pdf" if header[:4] == b"%PDF" else "image/png"
        return mime

    def process_image(self, image_path: str, language_hint: Optional[str] = None) -> OCRResponsePayload:
        if not image_path or not os.path.exists(image_path):
            raise FileNotFoundError(
                f"SarvamOCRProvider: file not found at '{image_path}'."
            )

        mime = self._get_mime(image_path)
        language = language_hint or self._detect_language(image_path)
        filename = os.path.basename(image_path)

        logger.info(
            f"[Sarvam] Processing '{filename}' ({mime}, lang={language}) "
            f"— running digitise + extract pipeline"
        )

        full_text = ""
        extracted_fields: List[FieldExtractionResult] = []

        # ── STAGE 1: Digitise (full OCR text) ────────────────────────────────
        try:
            with open(image_path, "rb") as f:
                digitise_job = self.client.doc_ai.digitise(
                    file=[(filename, f, mime)],
                    language=language,
                    output_format="md",
                )

            logger.info(f"[Sarvam] Digitise job submitted: {digitise_job.job_id}")
            dig_status = _poll_until_done(self.client, digitise_job.job_id)

            if dig_status in ("completed", "partially_completed"):
                dig_results = self.client.doc_ai.get_results(job_id=digitise_job.job_id)
                # The result for digitise is markdown text
                if hasattr(dig_results, "result") and dig_results.result:
                    full_text = str(dig_results.result)
                elif hasattr(dig_results, "markdown"):
                    full_text = str(dig_results.markdown)
                logger.info(
                    f"[Sarvam] Digitise complete: {len(full_text)} chars of text extracted"
                )
            else:
                logger.warning(f"[Sarvam] Digitise job ended with status: {dig_status}")

        except ApiError as e:
            logger.error(
                f"[Sarvam] Digitise API error {e.status_code}: {e.body}",
                exc_info=True,
            )
            # Don't abort — try extract stage anyway
        except Exception as e:
            logger.error(f"[Sarvam] Digitise stage error: {e}", exc_info=True)

        # ── STAGE 2: Extract (schema-based field extraction) ──────────────────
        try:
            with open(image_path, "rb") as f:
                extract_job = self.client.doc_ai.extract(
                    file=[(filename, f, mime)],
                    schema=json.dumps(LAND_RECORD_SCHEMA),
                    language=language,
                    output_format="json",
                )

            logger.info(f"[Sarvam] Extract job submitted: {extract_job.job_id}")
            ext_status = _poll_until_done(self.client, extract_job.job_id)

            if ext_status in ("completed", "partially_completed"):
                ext_results = self.client.doc_ai.get_results(job_id=extract_job.job_id)
                raw_result = None

                if hasattr(ext_results, "result") and ext_results.result is not None:
                    raw_result = ext_results.result
                elif hasattr(ext_results, "data"):
                    raw_result = ext_results.data

                logger.info(f"[Sarvam] Extract raw result: {raw_result}")

                if raw_result:
                    extracted_fields = self._map_extract_result_to_fields(raw_result)
                    logger.info(
                        f"[Sarvam] Extract complete: {len(extracted_fields)} fields mapped"
                    )
            else:
                logger.warning(f"[Sarvam] Extract job ended with status: {ext_status}")

        except ApiError as e:
            logger.error(
                f"[Sarvam] Extract API error {e.status_code}: {e.body}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(f"[Sarvam] Extract stage error: {e}", exc_info=True)

        # ── Fallback: if extract returned nothing, use regex on full_text ─────
        if not extracted_fields and full_text:
            logger.warning(
                "[Sarvam] Schema extraction returned no fields — "
                "falling back to regex NLP parser on digitised text."
            )
            extracted_fields = LandRecordExtractionParser.extract_fields_from_ocr(
                full_text=full_text,
                tokens=[],
                page_number=1,
                provider_name="sarvam_vision_fallback",
            )

        # Detect language from full_text if possible, else use hint
        detected_language = language.split("-")[0] if language else "hi"

        return OCRResponsePayload(
            full_text=full_text,
            detected_language=detected_language,
            tokens=[],   # Sarvam Vision doesn't expose per-token bboxes via SDK
            extracted_fields=extracted_fields,
            provider_name="Sarvam Vision 1.5 (Doc AI SDK)",
        )

    def _map_extract_result_to_fields(
        self, result: object
    ) -> List[FieldExtractionResult]:
        """
        Map the Sarvam extract() result object to FieldExtractionResult list.

        The result is either a dict or a pydantic model where each key
        matches our schema property names.
        """
        if isinstance(result, dict):
            data = result
        elif hasattr(result, "__dict__"):
            data = {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
        elif hasattr(result, "model_dump"):
            data = result.model_dump(exclude_none=True)
        else:
            logger.warning(f"[Sarvam] Unexpected result type: {type(result)}")
            return []

        fields: List[FieldExtractionResult] = []

        # Confidence heuristic: Sarvam Vision doesn't return per-field confidence.
        # We assign 0.92 for fields that are non-null (model is confident when it
        # returns a value) and 0.0 for null/missing (model couldn't find the field).
        for field_name, value in data.items():
            if field_name not in LAND_RECORD_SCHEMA["properties"]:
                continue  # Ignore unexpected fields

            str_value = str(value).strip() if value is not None else None

            if not str_value or str_value.lower() in ("none", "null", "", "unknown"):
                # Field not found in document — skip (do NOT invent a value)
                logger.debug(f"[Sarvam] Field '{field_name}' not found in document.")
                continue

            # For area: strip any accidentally included unit text
            if field_name == "plot_area":
                import re
                str_value = re.sub(r"[^\d\.\,]", "", str_value).strip("., ")
                if not str_value:
                    continue

            fields.append(
                FieldExtractionResult(
                    field_name=field_name,
                    value=str_value,
                    normalized_value=str_value,
                    confidence=0.92,   # Sarvam Vision 1.5 schema-extraction confidence
                    raw_text=str_value,
                    source_page=1,
                    bounding_box=[0, 0, 0, 0],   # Not available from SDK
                    extraction_method="sarvam_vision_schema_extract",
                    model_version="Sarvam_Vision_1.5",
                )
            )

        logger.info(
            f"[Sarvam] Mapped {len(fields)} non-null fields from extraction result"
        )
        return fields
