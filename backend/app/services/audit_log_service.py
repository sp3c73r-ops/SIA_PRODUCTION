from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import audit_log_repository

SENSITIVE_KEY_PATTERNS = {
    "password",
    "passwd",
    "mot_de_passe",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "secret",
    "authorization",
    "private_key",
    "file_content",
    "content_bytes",
}


def sanitize_sensitive_data(data: Any) -> Any:
    """
    Nettoie récursivement les données pour expurger les clés sensibles
    (mots de passe, tokens, secrets, etc.) avant enregistrement d'audit.
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            key_str = str(key).lower()
            if any(pattern in key_str for pattern in SENSITIVE_KEY_PATTERNS):
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = sanitize_sensitive_data(value)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


class AuditLogService:
    """
    Service d'audit backend.

    Responsabilités:
    - Enregistrer les événements d'audit en masquant toute donnée sensible.
    - S'intégrer dans la transaction de l'appelant via db.flush() sans forcer db.commit().
    - Garantir l'immutabilité applicative (aucune opération de mise à jour ni de suppression).
    - Ne jamais intervenir dans les décisions RBAC ni dans l'attribution de permissions.
    """

    def log_event(
        self,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
        document_id: Optional[int] = None,
        permission_request_id: Optional[int] = None,
        bureau_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        old_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        auto_commit: bool = False,
    ) -> AuditLog:
        if not action or not action.strip():
            raise ValueError("L'action d'audit est obligatoire.")
        if not entity_type or not entity_type.strip():
            raise ValueError("L'entity_type d'audit est obligatoire.")

        clean_old_state = sanitize_sensitive_data(old_state) if old_state is not None else None
        clean_new_state = sanitize_sensitive_data(new_state) if new_state is not None else None
        clean_metadata = sanitize_sensitive_data(metadata) if metadata is not None else None

        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action.strip(),
            entity_type=entity_type.strip(),
            entity_id=entity_id,
            document_id=document_id,
            permission_request_id=permission_request_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
            old_state=clean_old_state,
            new_state=clean_new_state,
            metadata=clean_metadata,
            request_id=request_id,
        )

        return audit_log_repository.create(db, audit_log, auto_commit=auto_commit)

    def get_by_id(self, db: Session, audit_log_id: int) -> Optional[AuditLog]:
        return audit_log_repository.get_by_id(db, audit_log_id)

    def get_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return audit_log_repository.get_by_entity(
            db, entity_type, entity_id, limit=limit, offset=offset
        )

    def get_by_document(
        self,
        db: Session,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return audit_log_repository.get_by_document_id(
            db, document_id, limit=limit, offset=offset
        )

    def get_by_permission_request(
        self,
        db: Session,
        permission_request_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return audit_log_repository.get_by_permission_request_id(
            db, permission_request_id, limit=limit, offset=offset
        )

    def list_logs(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        actor_user_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        bureau_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[AuditLog]:
        return audit_log_repository.list(
            db,
            limit=limit,
            offset=offset,
            actor_user_id=actor_user_id,
            circonscription_id=circonscription_id,
            bureau_id=bureau_id,
            entity_type=entity_type,
            action=action,
        )


audit_log_service = AuditLogService()
