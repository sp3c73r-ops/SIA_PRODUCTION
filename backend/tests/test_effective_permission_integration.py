from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.models.permission_request import PERMISSION_REQUEST_STATUS_APPROVED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_CANCELLED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_PENDING
from app.models.permission_request import PERMISSION_REQUEST_STATUS_REJECTED
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.security.authorization import has_effective_permission
from app.services.document_service import document_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _request(status: str, user_id: int, bureau_id: int, permission: str, document_id=None, expires_at=None):
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission=permission,
        status=status,
        document_id=document_id,
        expires_at=expires_at,
    )


class TestEffectivePermissionIntegration(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
            refresh=lambda _: None,
            add=lambda _: None,
        )

    # 1. USER avec permission permanente -> acces.
    def test_user_with_permanent_permission_has_access(self):
        user = _user(10, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with patch("app.services.document_service.document_repository.get_all", return_value=[SimpleNamespace(id=1, bureau_id=1)]):
            result = document_service.get_all(self.db, user)

        self.assertEqual(len(result), 1)

    # 2. USER sans permission permanente mais avec demande APPROVED non expiree -> acces.
    def test_user_with_valid_temporary_permission_has_access(self):
        user = _user(11, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved = _request(
            status=PERMISSION_REQUEST_STATUS_APPROVED,
            user_id=11,
            bureau_id=1,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved,
        ), patch(
            "app.services.document_service.document_repository.get_all",
            return_value=[SimpleNamespace(id=2, bureau_id=1)],
        ):
            result = document_service.get_all(self.db, user)

        self.assertEqual(len(result), 1)

    # 3. USER avec demande APPROVED expiree -> refus.
    def test_user_with_expired_temporary_permission_is_denied(self):
        user = _user(12, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved_expired = _request(
            status=PERMISSION_REQUEST_STATUS_APPROVED,
            user_id=12,
            bureau_id=1,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_expired,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=approved_expired,
        ) as mock_mark_expired:
            with self.assertRaises(HTTPException) as ctx:
                document_service.get_all(self.db, user)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_mark_expired.assert_called_once()

    # 4. USER avec permission temporaire pour bureau 2 essayant bureau 1 -> refus.
    def test_temporary_permission_other_bureau_is_denied(self):
        user = _user(13, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved_other_bureau = _request(
            status=PERMISSION_REQUEST_STATUS_APPROVED,
            user_id=13,
            bureau_id=2,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_other_bureau,
        ):
            allowed = has_effective_permission(
                self.db,
                user,
                "document.read",
                bureau_id=1,
            )

        self.assertFalse(allowed)

    # 5. ADMIN -> acces global.
    def test_admin_keeps_global_access(self):
        admin = _user(1, USER_ROLE_ADMIN, permissions=[], bureau_id=None)
        docs = [
            SimpleNamespace(id=21, bureau_id=1),
            SimpleNamespace(id=22, bureau_id=2),
        ]

        with patch("app.services.document_service.document_repository.get_all", return_value=docs) as mock_get_all:
            result = document_service.get_all(self.db, admin)

        self.assertEqual(len(result), 2)
        mock_get_all.assert_called_once_with(self.db, bureau_id=None)

    # 6. Une permission REJECTED -> refus.
    def test_rejected_temporary_permission_is_denied(self):
        user = _user(14, USER_ROLE_USER, permissions=[], bureau_id=1)
        rejected = _request(
            status=PERMISSION_REQUEST_STATUS_REJECTED,
            user_id=14,
            bureau_id=1,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=rejected,
        ):
            allowed = has_effective_permission(self.db, user, "document.read", bureau_id=1)

        self.assertFalse(allowed)

    # 7. Une permission CANCELLED -> refus.
    def test_cancelled_temporary_permission_is_denied(self):
        user = _user(15, USER_ROLE_USER, permissions=[], bureau_id=1)
        cancelled = _request(
            status=PERMISSION_REQUEST_STATUS_CANCELLED,
            user_id=15,
            bureau_id=1,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=cancelled,
        ):
            allowed = has_effective_permission(self.db, user, "document.read", bureau_id=1)

        self.assertFalse(allowed)

    # 8. Une permission PENDING -> refus.
    def test_pending_temporary_permission_is_denied(self):
        user = _user(16, USER_ROLE_USER, permissions=[], bureau_id=1)
        pending = _request(
            status=PERMISSION_REQUEST_STATUS_PENDING,
            user_id=16,
            bureau_id=1,
            permission="document.read",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=pending,
        ):
            allowed = has_effective_permission(self.db, user, "document.read", bureau_id=1)

        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
