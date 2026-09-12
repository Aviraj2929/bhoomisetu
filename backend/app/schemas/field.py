from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class FieldBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    field_name: str
    value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None
    source_bbox: Optional[List[int]] = None
    source_page: int = 1
    extraction_method: Optional[str] = "OCR_HYBRID"
    model_version: Optional[str] = "v1.0"

class FieldResponse(FieldBase):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    field_id: str
    document_id: str
    is_verified: bool
    verified_at: Optional[datetime] = None

class OCRTokenSchema(BaseModel):
    text: str
    confidence: float
    bbox: List[int]

class OCRResultsResponse(BaseModel):
    document_id: str
    full_text: str
    detected_language: str
    provider_name: str
    tokens: List[OCRTokenSchema]
