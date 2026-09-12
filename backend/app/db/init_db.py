from app.core.database import Base, engine
from app.models.user import User
from app.models.document import Document, DocumentPage
from app.models.extraction import ExtractedField
from app.models.audit import AuditLog
from app.models.correction import HumanCorrectionLog

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database tables...")
    init_db()
    print("Database tables created successfully.")
