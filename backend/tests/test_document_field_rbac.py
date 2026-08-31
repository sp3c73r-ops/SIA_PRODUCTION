from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.document_field_router import get_document_field
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER
from app.schemas.document_field_schema import DocumentFieldCreate, DocumentFieldUpdate
from app.services.document_field_service import document_field_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _field(field_id: int = 1):
    return SimpleNamespace(
        id=field_id,
        name="reference",
        label="Reference",
        field_type="string",
        active=True,
    )


def _approved_request(user_id: int, bureau_id: int, permission: str, expired=False):
    delta = -5 if expired else 10
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission=permission,
        status="APPROVED",
        document_id=None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=delta),
    )


class TestDocumentFieldRbac(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
            refresh=lambda _: None,
            add=lambda _: None,
            delete=lambda _: None,
        )

    def test_admin_can_read_document_fields(self):
        admin = _user(1, USER_ROLE_ADMIN)

        with patch(
            "app.services.document_field_service.document_field_repository.get_all",
            return_value=[_field()],
        ):
            result = document_field_service.get_all(self.db, admin)

        self.assertEqual(result[0].id, 1)

    def test_admin_can_create_document_field(self):
        admin = _user(1, USER_ROLE_ADMIN)
        data = DocumentFieldCreate(
            name="surface",
            label="Surface",
            field_type="decimal",
        )

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_name",
            return_value=None,
        ), patch(
            "app.services.document_field_service.document_field_repository.create",
            side_effect=lambda _, item: item,
        ):
            result = document_field_service.create(self.db, data, admin)

        self.assertEqual(result.name, "surface")

    def test_admin_can_update_document_field(self):
        admin = _user(1, USER_ROLE_ADMIN)
        field = _field()

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_id",
            return_value=field,
        ), patch(
            "app.services.document_field_service.document_field_repository.update",
            return_value=field,
        ):
            result = document_field_service.update(
                self.db,
                field.id,
                DocumentFieldUpdate(label="Nouvelle reference"),
                admin,
            )

        self.assertEqual(result.label, "Nouvelle reference")

    def test_admin_can_delete_document_field(self):
        admin = _user(1, USER_ROLE_ADMIN)
        field = _field()

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_id",
            return_value=field,
        ), patch(
            "app.services.document_field_service.document_field_value_repository.count_by_field_id",
            return_value=0,
        ), patch(
            "app.services.document_field_service.document_field_repository.delete",
            return_value=True,
        ):
            result = document_field_service.delete(self.db, field.id, admin)

        self.assertTrue(result)

    def test_user_with_read_permission_can_read_document_fields(self):
        user = _user(2, USER_ROLE_USER, ["document_field.read"], bureau_id=1)

        with patch(
            "app.services.document_field_service.document_field_repository.get_all",
            return_value=[_field()],
        ):
            result = document_field_service.get_all(self.db, user)

        self.assertEqual(len(result), 1)

    def test_user_with_create_permission_can_create_document_field(self):
        user = _user(2, USER_ROLE_USER, ["document_field.create"], bureau_id=1)
        data = DocumentFieldCreate(
            name="localisation",
            label="Localisation",
            field_type="string",
        )

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_name",
            return_value=None,
        ), patch(
            "app.services.document_field_service.document_field_repository.create",
            side_effect=lambda _, item: item,
        ):
            result = document_field_service.create(self.db, data, user)

        self.assertEqual(result.name, "localisation")

    def test_user_with_update_permission_can_update_document_field(self):
        user = _user(2, USER_ROLE_USER, ["document_field.update"], bureau_id=1)
        field = _field()

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_id",
            return_value=field,
        ), patch(
            "app.services.document_field_service.document_field_repository.update",
            return_value=field,
        ):
            result = document_field_service.update(
                self.db,
                field.id,
                DocumentFieldUpdate(active=False),
                user,
            )

        self.assertFalse(result.active)

    def test_user_with_delete_permission_can_delete_document_field(self):
        user = _user(2, USER_ROLE_USER, ["document_field.delete"], bureau_id=1)
        field = _field()

        with patch(
            "app.services.document_field_service.document_field_repository.get_by_id",
            return_value=field,
        ), patch(
            "app.services.document_field_service.document_field_value_repository.count_by_field_id",
            return_value=0,
        ), patch(
            "app.services.document_field_service.document_field_repository.delete",
            return_value=True,
        ):
            result = document_field_service.delete(self.db, field.id, user)

        self.assertTrue(result)

    def test_user_without_read_permission_is_forbidden(self):
        user = _user(3, USER_ROLE_USER, [], bureau_id=1)
        self._assert_forbidden(document_field_service.get_all, self.db, user)

    def test_user_without_create_permission_is_forbidden(self):
        user = _user(3, USER_ROLE_USER, [], bureau_id=1)
        data = DocumentFieldCreate(name="code", label="Code", field_type="string")
        self._assert_forbidden(document_field_service.create, self.db, data, user)

    def test_user_without_update_permission_is_forbidden(self):
        user = _user(3, USER_ROLE_USER, [], bureau_id=1)
        self._assert_forbidden(
            document_field_service.update,
            self.db,
            1,
            DocumentFieldUpdate(label="Interdit"),
            user,
        )

    def test_user_without_delete_permission_is_forbidden(self):
        user = _user(3, USER_ROLE_USER, [], bureau_id=1)
        self._assert_forbidden(document_field_service.delete, self.db, 1, user)

    def test_user_with_valid_temporary_read_permission_is_allowed(self):
        user = _user(4, USER_ROLE_USER, [], bureau_id=1)
        request = _approved_request(4, 1, "document_field.read")

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=request,
        ), patch(
            "app.services.document_field_service.document_field_repository.get_all",
            return_value=[],
        ):
            result = document_field_service.get_all(self.db, user)

        self.assertEqual(result, [])

    def test_user_with_expired_temporary_read_permission_is_forbidden(self):
        user = _user(5, USER_ROLE_USER, [], bureau_id=1)
        request = _approved_request(5, 1, "document_field.read", expired=True)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=request,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=request,
        ) as mark_expired:
            with self.assertRaises(HTTPException) as context:
                document_field_service.get_all(self.db, user)

        self.assertEqual(context.exception.status_code, 403)

        mark_expired.assert_called_once_with(self.db, request)

    def test_temporary_permission_from_another_bureau_is_forbidden(self):
        user = _user(6, USER_ROLE_USER, [], bureau_id=1)
        request = _approved_request(6, 2, "document_field.read")

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=request,
        ):
            self._assert_forbidden(document_field_service.get_all, self.db, user)

    def test_unknown_document_field_returns_404(self):
        admin = _user(1, USER_ROLE_ADMIN)

        with patch(
            "app.api.document_field_router.document_field_service.get_by_id",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as context:
                get_document_field(999, self.db, admin)

        self.assertEqual(context.exception.status_code, 404)

    def _assert_forbidden(self, operation, *args):
        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as context:
                operation(*args)

        self.assertEqual(context.exception.status_code, 403)