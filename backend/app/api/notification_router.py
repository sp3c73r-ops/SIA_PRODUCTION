from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.repositories.notification_repository import notification_repository
from app.schemas.notification_schema import (
    NotificationMarkAllReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.security.authorization import require_permission
from app.security.permissions import (
    PERMISSION_NOTIFICATION_MARK_READ,
    PERMISSION_NOTIFICATION_READ,
)
from app.services.notification_service import notification_service


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=List[NotificationResponse],
)
def list_my_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_NOTIFICATION_READ)
    ),
):
    return notification_service.list_my_notifications(
        db,
        current_user,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
)
def count_my_unread_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_NOTIFICATION_READ)
    ),
):
    count = notification_service.count_my_unread(
        db,
        current_user,
    )
    return {"unread_count": count}


@router.patch(
    "/read-all",
    response_model=NotificationMarkAllReadResponse,
)
def mark_all_my_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_NOTIFICATION_MARK_READ)
    ),
):
    updated_count = notification_service.mark_all_as_read(
        db,
        current_user,
    )
    return {"updated_count": updated_count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_NOTIFICATION_MARK_READ)
    ),
):
    notif = notification_repository.get_by_id(db, notification_id)
    if notif is None:
        raise HTTPException(
            status_code=404,
            detail="Notification introuvable",
        )

    if notif.recipient_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Acces interdit a cette notification.",
        )

    notification_service.mark_as_read(
        db,
        notification_id,
        current_user,
    )
    db.refresh(notif)
    return notif
