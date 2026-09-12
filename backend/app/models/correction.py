import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from app.core.database import Base

class HumanCorrectionLog(Base):
    __tablename__ = "human_corrections"

    correction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_id = Column(String(36), ForeignKey("extracted_fields.field_id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=False)
    verifier_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    
    field_name = Column(String(100), nullable=False)
    ai_original_value = Column(Text, nullable=True)
    human_corrected_value = Column(Text, nullable=False)
    reason = Column(String(255), default="Verifier manual edit")
    
    source_bbox = Column(JSON, nullable=True)
    model_version = Column(String(50), default="Sarvam_v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
