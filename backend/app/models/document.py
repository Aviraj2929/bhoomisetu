import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import DocumentStatus

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    document_type = Column(String(100), default="UNKNOWN")
    
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    overall_confidence = Column(Float, default=0.0)
    
    uploaded_by_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")

class DocumentPage(Base):
    __tablename__ = "document_pages"

    page_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_storage_path = Column(String(512), nullable=False)
    width_pixels = Column(Integer, default=0)
    height_pixels = Column(Integer, default=0)

    document = relationship("Document", back_populates="pages")
