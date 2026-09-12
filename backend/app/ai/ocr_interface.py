from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class OCRToken(BaseModel):
    text: str
    confidence: float
    bbox: List[int]  # [x_min, y_min, x_max, y_max]

class FieldExtractionResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    field_name: str
    value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = 0.0
    raw_text: str = ""
    source_page: int = 1
    bounding_box: List[int] = [0, 0, 0, 0]
    extraction_method: str = "OCR_REGIONAL_PARSER"
    model_version: str = "Sarvam_v1.0"

class OCRResponsePayload(BaseModel):
    full_text: str
    detected_language: str
    tokens: List[OCRToken]
    extracted_fields: List[FieldExtractionResult]
    provider_name: str

class OCRProvider(ABC):
    """Abstract Base Class Interface for OCR/HTR Engine Providers."""

    @abstractmethod
    def process_image(self, image_path: str, language_hint: Optional[str] = None) -> OCRResponsePayload:
        pass
