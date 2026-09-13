from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.circonscription_router import get_circonscriptions
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER
from app.schemas.circonscription_schema import CirconscriptionCreate
from app.services.circonscription_service import circonscription_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _circonscription(circonscription_id: int, nom: str):
    return SimpleNamespace(id=circonscription_id, nom=nom)


def _approved_request(user_id: int, bureau_id: int, expired=False):
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission="document.read",
        status="APPROVED",
        document_id=None,
        expires_at=datetime.now(timezone.utc) + timedelta(
            minutes=-5 if expired else 10
        ),
    )


class TestCirconscriptionRbac(unittest.TestCase):

    def test_admin_can_list_all_circonscriptions(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN)
        expected = [_circonscription(1, "Gombe"), _circonscription(2, "Limete")]

        with patch(
            "app.services.circonscription_service.circonscription_repository.get_all",
            return_value=expected,
        ) as get_all:
            result = circonscription_service.get_all(db, admin)

        self.assertEqual(result, expected)
        get_all.assert_called_once_with(db)

    def test_gombe_user_sees_only_gombe(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["document.read"], bureau_id=1)
        gombe = _circonscription(1, "Gombe")

        with patch(
            "app.services.circonscription_service.circonscription_repository.get_by_bureau_id",
            return_value=gombe,
        ) as get_by_bureau:
            result = circonscription_service.get_all(db, user)

        self.assertEqual(result, [gombe])
        get_by_bureau.assert_called_once_with(db, 1)

    def test_user_scope_is_derived_from_server_bureau(self):
        db = SimpleNamespace()
        user = _user(3, USER_ROLE_USER, ["document.read"], bureau_id=3)
        gombe = _circonscription(1, "Gombe")

        with patch(
            "app.services.circonscription_service.circonscription_repository.get_by_bureau_id",
            return_value=gombe,
        ) as get_by_bureau:
            get_circonscriptions(db, user)

        get_by_bureau.assert_called_once_with(db, 3)

    def test_user_without_bureau_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["document.read"])

        with self.assertRaises(HTTPException) as context:
            circonscription_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_user_without_document_read_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ), self.assertRaises(HTTPException) as context:
            circonscription_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_valid_temporary_document_read_allows_own_circonscription(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)
        gombe = _circonscription(1, "Gombe")

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 1),
        ), patch(
            "app.services.circonscription_service.circonscription_repository.get_by_bureau_id",
            return_value=gombe,
        ):
            result = circonscription_service.get_all(db, user)

        self.assertEqual(result, [gombe])

    def test_expired_temporary_document_read_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 1, expired=True),
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
        ) as mark_expired, self.assertRaises(HTTPException) as context:
            circonscription_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)
        mark_expired.assert_called_once()

    def test_user_cannot_create_circonscription(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["document.read"], bureau_id=1)
        data = CirconscriptionCreate(nom="Interdit")

        with self.assertRaises(HTTPException) as context:
            circonscription_service.create(db, data, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_admin_can_create_circonscription(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN)
        data = CirconscriptionCreate(nom="Nouvelle")
        created = _circonscription(8, "Nouvelle")

        with patch(
            "app.services.circonscription_service.circonscription_repository.create",
            return_value=created,
        ) as create:
            result = circonscription_service.create(db, data, admin)

        self.assertEqual(result, created)
        self.assertEqual(create.call_args.args[1].nom, "Nouvelle")