from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    """
    Repository pour l'accès aux données et la persistance des notifications.
    """

    def create(
        self,
        db: Session,
        notification: Notification,
        auto_commit: bool = True,
    ) -> Notification:
        db.add(notification)
        if auto_commit:
            db.commit()
            db.refresh(notification)
        else:
            db.flush()
        return notification

    def create_many(
        self,
        db: Session,
        notifications: List[Notification],
        auto_commit: bool = True,
    ) -> List[Notification]:
        if not notifications:
            return []
        db.add_all(notifications)
        if auto_commit:
            db.commit()
        else:
            db.flush()
        return notifications

    def get_by_id(
        self,
        db: Session,
        notification_id: int,
    ) -> Optional[Notification]:
        return (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def list_for_recipient(
        self,
        db: Session,
        recipient_user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> List[Notification]:
        query = db.query(Notification).filter(
            Notification.recipient_user_id == recipient_user_id
        )

        if unread_only:
            query = query.filter(Notification.read_at.is_(None))

        return (
            query.order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_unread_for_recipient(
        self,
        db: Session,
        recipient_user_id: int,
    ) -> int:
        return (
            db.query(func.count(Notification.id))
            .filter(
                Notification.recipient_user_id == recipient_user_id,
                Notification.read_at.is_(None),
            )
            .scalar()
            or 0
        )

    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        recipient_user_id: int,
        auto_commit: bool = True,
    ) -> bool:
        now = datetime.now(timezone.utc)
        updated_count = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.recipient_user_id == recipient_user_id,
                Notification.read_at.is_(None),
            )
            .update(
                {Notification.read_at: now},
                synchronize_session=False,
            )
        )

        if updated_count > 0:
            if auto_commit:
                db.commit()
            else:
                db.flush()
            return True

        return False

    def mark_all_as_read(
        self,
        db: Session,
        recipient_user_id: int,
        auto_commit: bool = True,
    ) -> int:
        now = datetime.now(timezone.utc)
        updated_count = (
            db.query(Notification)
            .filter(
                Notification.recipient_user_id == recipient_user_id,
                Notification.read_at.is_(None),
            )
            .update(
                {Notification.read_at: now},
                synchronize_session=False,
            )
        )

        if updated_count > 0:
            if auto_commit:
                db.commit()
            else:
                db.flush()

        return updated_count


notification_repository = NotificationRepository()
