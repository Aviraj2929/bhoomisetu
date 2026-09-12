import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    field_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, default=1)
    
    field_name = Column(String(100), nullable=False, index=True) # e.g. owner_name, survey_number, khata_number
    value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0, index=True)
    raw_text = Column(Text, nullable=True)
    source_bbox = Column(JSON, nullable=True) # [x_min, y_min, x_max, y_max]
    extraction_method = Column(String(100), default="OCR_HYBRID")
    model_version = Column(String(50), default="Sarvam_v1.0")

    is_verified = Column(Boolean, default=False)
    verified_by_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="extracted_fields")
