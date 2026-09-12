from typing import List, Optional
import os
import shutil
import hashlib
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.enums import DocumentStatus

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.document_id == document_id).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> List[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, filename: str, size: int, mime_type: str, file_hash: str, storage_path: str) -> Document:
        doc = Document(
            original_filename=filename,
            file_size_bytes=size,
            mime_type=mime_type,
            file_hash_sha256=file_hash,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
            overall_confidence=0.0
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_status(self, document_id: str, status: DocumentStatus, confidence: float = 0.0) -> Optional[Document]:
        doc = self.get_by_id(document_id)
        if doc:
            doc.status = status
            doc.overall_confidence = confidence
            self.db.commit()
            self.db.refresh(doc)
        return doc
