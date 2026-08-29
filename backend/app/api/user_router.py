from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
)
from app.services.user_service import user_service


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/",
    response_model=List[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
):
    return user_service.repository.get_all(db)


@router.post(
    "/",
    response_model=UserResponse,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):

    try:
        return user_service.create(db, data)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )