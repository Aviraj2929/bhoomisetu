import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(100), nullable=False) # e.g. document, extracted_field
    entity_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False) # e.g. UPLOAD, VERIFY, REJECT
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    changes = Column(JSON, nullable=True)
    client_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
