from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import USER_ROLE_ADMIN, User
from app.repositories.notification_repository import notification_repository
from app.security.authorization import has_effective_permission
from app.security.permissions import (
    PERMISSION_NOTIFICATION_MARK_READ,
    PERMISSION_NOTIFICATION_READ,
)


class NotificationService:
    """
    Service métier pour la gestion des notifications utilisateur.
    
    Responsabilités :
    - Validation des entrées et sécurité RBAC (notification.read / notification.mark_read).
    - Isolation stricte des destinataires (current_user.id).
    - Notification ciblée individuelle ou multi-administrateurs de circonscription.
    - Intégration neutre dans les transactions parentes via auto_commit=False.
    """

    def _ensure_permission(self, db: Session, current_user: User, permission: str):
        if not has_effective_permission(db, current_user, permission):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse.",
            )

    def notify_user(
        self,
        db: Session,
        recipient_user_id: int,
        action: str,
        title: str,
        message: str,
        permission_request_id: Optional[int] = None,
        document_id: Optional[int] = None,
        bureau_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        auto_commit: bool = True,
    ) -> Notification:
        if not recipient_user_id or recipient_user_id <= 0:
            raise ValueError("recipient_user_id doit être un identifiant valide.")
        if not action or not action.strip():
            raise ValueError("L'action de notification est obligatoire.")
        if not title or not title.strip():
            raise ValueError("Le titre de notification est obligatoire.")
        if not message or not message.strip():
            raise ValueError("Le message de notification est obligatoire.")

        notification = Notification(
            recipient_user_id=recipient_user_id,
            action=action.strip(),
            title=title.strip(),
            message=message.strip(),
            permission_request_id=permission_request_id,
            document_id=document_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return notification_repository.create(
            db, notification, auto_commit=auto_commit
        )

    def notify_admins_of_circonscription(
        self,
        db: Session,
        circonscription_id: int,
        action: str,
        title: str,
        message: str,
        permission_request_id: Optional[int] = None,
        document_id: Optional[int] = None,
        bureau_id: Optional[int] = None,
        auto_commit: bool = True,
    ) -> List[Notification]:
        if not circonscription_id or circonscription_id <= 0:
            raise ValueError("circonscription_id doit être un identifiant valide.")
        if not action or not action.strip():
            raise ValueError("L'action de notification est obligatoire.")
        if not title or not title.strip():
            raise ValueError("Le titre de notification est obligatoire.")
        if not message or not message.strip():
            raise ValueError("Le message de notification est obligatoire.")

        admins = (
            db.query(User)
            .filter(
                User.role == USER_ROLE_ADMIN,
                User.admin_circonscription_id == circonscription_id,
                User.actif == True,
            )
            .all()
        )

        if not admins:
            return []

        notifications = [
            Notification(
                recipient_user_id=admin.id,
                action=action.strip(),
                title=title.strip(),
                message=message.strip(),
                permission_request_id=permission_request_id,
                document_id=document_id,
                bureau_id=bureau_id,
                circonscription_id=circonscription_id,
            )
            for admin in admins
        ]

        return notification_repository.create_many(
            db, notifications, auto_commit=auto_commit
        )

    def list_my_notifications(
        self,
        db: Session,
        current_user: User,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> List[Notification]:
        self._ensure_permission(db, current_user, PERMISSION_NOTIFICATION_READ)
        return notification_repository.list_for_recipient(
            db,
            recipient_user_id=current_user.id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
        )

    def count_my_unread(
        self,
        db: Session,
        current_user: User,
    ) -> int:
        self._ensure_permission(db, current_user, PERMISSION_NOTIFICATION_READ)
        return notification_repository.count_unread_for_recipient(
            db, recipient_user_id=current_user.id
        )

    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        current_user: User,
        auto_commit: bool = True,
    ) -> bool:
        self._ensure_permission(db, current_user, PERMISSION_NOTIFICATION_MARK_READ)
        return notification_repository.mark_as_read(
            db,
            notification_id=notification_id,
            recipient_user_id=current_user.id,
            auto_commit=auto_commit,
        )

    def mark_all_as_read(
        self,
        db: Session,
        current_user: User,
        auto_commit: bool = True,
    ) -> int:
        self._ensure_permission(db, current_user, PERMISSION_NOTIFICATION_MARK_READ)
        return notification_repository.mark_all_as_read(
            db,
            recipient_user_id=current_user.id,
            auto_commit=auto_commit,
        )


notification_service = NotificationService()
