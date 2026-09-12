from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.enums import DocumentStatus

class DocumentBase(BaseModel):
    original_filename: str
    file_size_bytes: int
    mime_type: str

class DocumentCreate(DocumentBase):
    file_hash_sha256: str
    storage_path: str

class DocumentResponse(DocumentBase):
    document_id: str
    status: DocumentStatus
    overall_confidence: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    overall_confidence: float
    message: Optional[str] = None
