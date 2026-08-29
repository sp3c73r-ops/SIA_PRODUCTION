from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.phase_schema import (
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
)
from app.services.phase_service import phase_service


router = APIRouter(
    prefix="/phases",
    tags=["Phases"],
)


@router.get(
    "/",
    response_model=List[PhaseResponse],
)
def get_phases(
    db: Session = Depends(get_db),
):
    return phase_service.repository.get_all(db)


@router.post(
    "/",
    response_model=PhaseResponse,
)
def create_phase(
    data: PhaseCreate,
    db: Session = Depends(get_db),
):
    try:
        return phase_service.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{phase_id}",
    response_model=PhaseResponse,
)
def update_phase(
    phase_id: int,
    data: PhaseUpdate,
    db: Session = Depends(get_db),
):
    try:
        phase = phase_service.update(db, phase_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not phase:
        raise HTTPException(
            status_code=404,
            detail="Nature introuvable.",
        )

    return phase


@router.delete(
    "/{phase_id}",
)
def delete_phase(
    phase_id: int,
    db: Session = Depends(get_db),
):
    try:
        deleted = phase_service.delete(db, phase_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Nature introuvable.",
        )

    return {"message": "Nature supprimée."}