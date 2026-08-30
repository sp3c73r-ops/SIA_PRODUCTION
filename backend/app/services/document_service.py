from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_field_value import DocumentFieldValue
from app.models.user import User
from app.repositories.document_field_repository import (
    document_field_repository,
)
from app.repositories.document_field_value_repository import (
    document_field_value_repository,
)

from app.repositories.document_repository import (
    document_repository
)
from app.security.authorization import has_permission
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_DOCUMENT_CREATE
from app.security.permissions import PERMISSION_DOCUMENT_DELETE
from app.security.permissions import PERMISSION_DOCUMENT_READ
from app.security.permissions import PERMISSION_DOCUMENT_UPDATE

from app.schemas.document_schema import (
    DocumentCreate,
    DocumentUpdate,
)


class DocumentService:

    logger = logging.getLogger(__name__)

    TYPE_TO_COLUMN = {
        "string": "value_string",
        "text": "value_text",
        "integer": "value_integer",
        "decimal": "value_decimal",
        "date": "value_date",
        "datetime": "value_datetime",
        "boolean": "value_boolean",
    }

    def _ensure_permission(
        self,
        current_user: User,
        permission: str,
    ):
        if not has_permission(
            current_user,
            permission,
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

    def _get_scope_bureau_id(
        self,
        current_user: User,
    ) -> Optional[int]:
        if is_admin(current_user):
            return None

        user_bureau_id = getattr(
            current_user,
            "bureau_id",
            None,
        )

        if user_bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )

        return user_bureau_id

    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() == ""

        return False

    def _coerce_value(
        self,
        field_type: str,
        raw_value: Any,
    ):
        if field_type in {"string", "text"}:
            return str(raw_value).strip()

        if field_type == "integer":
            if isinstance(raw_value, bool):
                raise ValueError()
            return int(raw_value)

        if field_type == "decimal":
            if isinstance(raw_value, bool):
                raise ValueError()
            return Decimal(str(raw_value))

        if field_type == "date":
            if isinstance(raw_value, date) and not isinstance(raw_value, datetime):
                return raw_value

            if isinstance(raw_value, str):
                return date.fromisoformat(raw_value)

            raise ValueError()

        if field_type == "datetime":
            if isinstance(raw_value, datetime):
                return raw_value

            if isinstance(raw_value, str):
                return datetime.fromisoformat(raw_value)

            raise ValueError()

        if field_type == "boolean":
            if isinstance(raw_value, bool):
                return raw_value

            if isinstance(raw_value, str):
                lowered = raw_value.strip().lower()
                if lowered in {"true", "1", "yes", "oui"}:
                    return True
                if lowered in {"false", "0", "no", "non"}:
                    return False

            raise ValueError()

        raise ValueError()

    def _build_field_maps(self, fields):
        field_by_name = {}
        field_by_id = {}

        for field in fields:
            field_by_name[field.name] = field
            field_by_id[field.id] = field

        return field_by_name, field_by_id

    def _validate_required_fields(
        self,
        active_fields,
        custom_fields_payload: dict[str, Any],
        existing_values_by_name: Optional[dict[str, Any]] = None,
    ):
        existing_values_by_name = existing_values_by_name or {}

        for field in active_fields:
            if not field.required:
                continue

            if field.name in custom_fields_payload:
                value = custom_fields_payload[field.name]
            else:
                value = existing_values_by_name.get(field.name)

            if self._is_empty(value):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Le champ personnalisé '{field.label}' est obligatoire."
                    ),
                )

    def _apply_custom_fields(
        self,
        db: Session,
        document: Document,
        custom_fields_payload: dict[str, Any],
        allowed_fields,
    ):
        self.logger.info(
            "custom_fields_apply_start document_id=%s payload_keys=%s",
            document.id,
            list(custom_fields_payload.keys()),
        )

        allowed_by_name, _ = self._build_field_maps(allowed_fields)
        allowed_names = set(allowed_by_name.keys())

        for field_name, raw_value in custom_fields_payload.items():
            if field_name not in allowed_names:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Le champ personnalisé '{field_name}' n'est pas autorisé."
                    ),
                )

            field = allowed_by_name[field_name]

            self.logger.info(
                "custom_fields_resolved document_id=%s field_name=%s field_id=%s field_type=%s",
                document.id,
                field_name,
                field.id,
                field.field_type,
            )

            existing_row = (
                document_field_value_repository.get_by_document_and_field(
                    db,
                    document.id,
                    field.id,
                )
                if document.id is not None
                else None
            )

            if self._is_empty(raw_value):
                if field.required:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Le champ personnalisé '{field.label}' est obligatoire."
                        ),
                    )

                if existing_row is not None:
                    self.logger.info(
                        "custom_fields_delete_empty document_id=%s field_id=%s",
                        document.id,
                        field.id,
                    )
                    db.delete(existing_row)
                continue

            try:
                coerced_value = self._coerce_value(
                    field.field_type,
                    raw_value,
                )
            except (
                ValueError,
                TypeError,
                InvalidOperation,
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Valeur invalide pour le champ '{field.label}' ({field.field_type})."
                    ),
                )

            target_column = self.TYPE_TO_COLUMN[field.field_type]

            if existing_row is None:
                existing_row = DocumentFieldValue(
                    document_id=document.id,
                    document_field_id=field.id,
                )
                db.add(existing_row)
                self.logger.info(
                    "custom_fields_create_row document_id=%s field_id=%s",
                    document.id,
                    field.id,
                )
            else:
                self.logger.info(
                    "custom_fields_update_row document_id=%s field_id=%s row_id=%s",
                    document.id,
                    field.id,
                    existing_row.id,
                )

            # Une seule colonne de valeur doit être renseignée
            # selon le type du champ personnalisé.
            for column_name in self.TYPE_TO_COLUMN.values():
                setattr(existing_row, column_name, None)

            setattr(
                existing_row,
                target_column,
                coerced_value,
            )

            self.logger.info(
                "custom_fields_set_value document_id=%s field_id=%s target_column=%s",
                document.id,
                field.id,
                target_column,
            )

        db.flush()

        self.logger.info(
            "custom_fields_apply_done document_id=%s",
            document.id,
        )

    # ============================================================
    # CREATION
    # ============================================================

    def create(
        self,
        db: Session,
        data: DocumentCreate,
        current_user: User,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_CREATE,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        document_data = data.model_dump()
        custom_fields_payload = document_data.pop(
            "custom_fields",
            {},
        )

        if custom_fields_payload is None:
            custom_fields_payload = {}

        if not isinstance(custom_fields_payload, dict):
            raise HTTPException(
                status_code=400,
                detail="custom_fields doit être un objet clé/valeur.",
            )

        active_fields = document_field_repository.get_active(db)
        self.logger.info(
            "custom_fields_create_received custom_fields=%s active_fields_count=%s",
            custom_fields_payload,
            len(active_fields),
        )

        self._validate_required_fields(
            active_fields,
            custom_fields_payload,
        )

        # L'encodeur est déterminé par l'utilisateur authentifié.
        document_data.pop(
            "encodeur_id",
            None
        )

        # Un USER ne peut créer que dans son propre bureau.
        if scope_bureau_id is not None:
            document_data["bureau_id"] = scope_bureau_id

        document = Document(
            **document_data,
            encodeur_id=current_user.id,
        )

        created_document = document_repository.create(
            db,
            document,
        )

        self._apply_custom_fields(
            db,
            created_document,
            custom_fields_payload,
            active_fields,
        )

        db.commit()

        return document_repository.get_by_id(
            db,
            created_document.id,
        )

    # ============================================================
    # LISTE
    # ============================================================

    def get_all(
        self,
        db: Session,
        current_user: User,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_READ,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        return document_repository.get_all(
            db,
            bureau_id=scope_bureau_id,
        )

    # ============================================================
    # RECHERCHE AVANCEE
    # ============================================================

    def search(
        self,
        db: Session,
        current_user: User,
        reference_archive: Optional[str] = None,
        nom_document: Optional[str] = None,
        code_foncier: Optional[str] = None,
        numero_ordre: Optional[str] = None,
        type_document_id: Optional[int] = None,
        phase_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        date_debut=None,
        date_fin=None,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_READ,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        return document_repository.search(
            db=db,
            bureau_id=scope_bureau_id,
            reference_archive=reference_archive,
            nom_document=nom_document,
            code_foncier=code_foncier,
            numero_ordre=numero_ordre,
            type_document_id=type_document_id,
            phase_id=phase_id,
            circonscription_id=circonscription_id,
            date_debut=date_debut,
            date_fin=date_fin,
        )

    # ============================================================
    # PAR ID
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        document_id: int,
        current_user: User,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_READ,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        document = document_repository.get_by_id(
            db,
            document_id,
            bureau_id=scope_bureau_id,
        )

        if document:
            return document

        if scope_bureau_id is not None:
            existing_document = document_repository.get_by_id(
                db,
                document_id,
            )
            if existing_document is not None:
                raise HTTPException(
                    status_code=403,
                    detail="Acces interdit a ce document.",
                )

        return None

    # ============================================================
    # MODIFICATION
    # ============================================================

    def update(
        self,
        db: Session,
        document_id: int,
        data: DocumentUpdate,
        current_user: User,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_UPDATE,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        document = document_repository.get_by_id(
            db,
            document_id,
            bureau_id=scope_bureau_id,
        )

        if not document:
            if scope_bureau_id is not None:
                existing_document = document_repository.get_by_id(
                    db,
                    document_id,
                )
                if existing_document is not None:
                    raise HTTPException(
                        status_code=403,
                        detail="Acces interdit a ce document.",
                    )
            return None

        update_data = data.model_dump(
            exclude_unset=True
        )
        custom_fields_payload = update_data.pop(
            "custom_fields",
            None,
        )

        if (
            custom_fields_payload is not None
            and not isinstance(custom_fields_payload, dict)
        ):
            raise HTTPException(
                status_code=400,
                detail="custom_fields doit être un objet clé/valeur.",
            )

        for key, value in update_data.items():

            setattr(
                document,
                key,
                value,
            )

        active_fields = document_field_repository.get_active(db)
        self.logger.info(
            "custom_fields_update_received document_id=%s custom_fields=%s active_fields_count=%s",
            document.id,
            custom_fields_payload,
            len(active_fields),
        )

        existing_values = document_field_value_repository.get_by_document_id(
            db,
            document.id,
        )

        existing_values_by_name = {}
        used_field_ids = []
        for item in existing_values:
            if item.document_field:
                used_field_ids.append(item.document_field_id)
                existing_values_by_name[
                    item.document_field.name
                ] = Document._extract_typed_value(item)

        if custom_fields_payload is None:
            custom_fields_payload = {}

        self._validate_required_fields(
            active_fields,
            custom_fields_payload,
            existing_values_by_name,
        )

        used_fields = document_field_repository.get_by_ids(
            db,
            used_field_ids,
        )

        allowed_fields = {
            field.id: field
            for field in active_fields
        }

        for field in used_fields:
            allowed_fields[field.id] = field

        self._apply_custom_fields(
            db,
            document,
            custom_fields_payload,
            list(allowed_fields.values()),
        )

        updated_document = document_repository.update(
            db,
            document,
        )

        return document_repository.get_by_id(
            db,
            updated_document.id,
        )

    # ============================================================
    # SUPPRESSION
    # ============================================================

    def delete(
        self,
        db: Session,
        document_id: int,
        current_user: User,
    ):

        self._ensure_permission(
            current_user,
            PERMISSION_DOCUMENT_DELETE,
        )

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        document = document_repository.get_by_id(
            db,
            document_id,
            bureau_id=scope_bureau_id,
        )

        if not document:
            if scope_bureau_id is not None:
                existing_document = document_repository.get_by_id(
                    db,
                    document_id,
                )
                if existing_document is not None:
                    raise HTTPException(
                        status_code=403,
                        detail="Acces interdit a ce document.",
                    )
            return False

        return document_repository.delete(
            db,
            document,
        )


document_service = DocumentService()