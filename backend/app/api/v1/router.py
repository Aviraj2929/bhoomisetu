from fastapi import APIRouter
from app.api.v1.endpoints import documents, verification, records, dashboard

api_router = APIRouter()

api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(verification.router, prefix="/verification", tags=["Verification"])
api_router.include_router(records.router, prefix="/records", tags=["Land Records"])
api_router.include_router(dashboard.router, prefix="/analytics", tags=["Analytics & Dashboard"])
