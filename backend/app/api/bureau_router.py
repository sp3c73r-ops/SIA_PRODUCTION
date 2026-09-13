from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.bureau_schema import BureauCreate, BureauResponse, BureauUpdate
from app.security.dependencies import get_current_user
from app.services.bureau_service import bureau_service


router = APIRouter(prefix="/bureaux", tags=["Bureaux"])


@router.get("/", response_model=List[BureauResponse])
def get_bureaux(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return bureau_service.get_all(db, current_user)


@router.get("/{bureau_id}", response_model=BureauResponse)
def get_bureau(bureau_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return bureau_service.get_by_id(db, bureau_id, current_user)


@router.post("/", response_model=BureauResponse)
def create_bureau(data: BureauCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return bureau_service.create(db, data, current_user)


@router.patch("/{bureau_id}", response_model=BureauResponse)
def update_bureau(bureau_id: int, data: BureauUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return bureau_service.update(db, bureau_id, data, current_user)


@router.patch("/{bureau_id}/disable", response_model=BureauResponse)
def disable_bureau(bureau_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return bureau_service.disable(db, bureau_id, current_user)