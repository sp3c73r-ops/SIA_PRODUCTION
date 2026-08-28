from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import traceback

from app.database.session import get_db
from app.services.document_type_service import DocumentTypeService

router = APIRouter(
    prefix="/document-types",
    tags=["Document Types"]
)

service = DocumentTypeService()


@router.get("/")
def get_document_types(db: Session = Depends(get_db)):
    try:
        return service.repository.get_all(db)
    except Exception as e:
        traceback.print_exc()
        return {
            "error": str(e),
            "type": type(e).__name__
        }