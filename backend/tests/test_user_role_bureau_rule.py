from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.schemas.user_schema import UserCreate
from app.services.user_service import user_service


def _db_with_bureau_exists():
    db = MagicMock()
    query = MagicMock()
    query.filter.return_value.first.return_value = SimpleNamespace(id=2)
    db.query.return_value = query
    return db


class TestUserRoleBureauRule(unittest.TestCase):

    # Schema: ADMIN + bureau_id NULL => OK
    def test_schema_admin_without_bureau_is_allowed(self):
        user = UserCreate(
            nom="Admin",
            prenom="Root",
            username="admin.root",
            password="secret",
            role=USER_ROLE_ADMIN,
            bureau_id=None,
            permissions=[],
        )
        self.assertEqual(user.role, USER_ROLE_ADMIN)
        self.assertIsNone(user.bureau_id)

    # Schema: ADMIN + bureau_id renseigne => refus
    def test_schema_admin_with_bureau_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                nom="Admin",
                prenom="Root",
                username="admin.bureau",
                password="secret",
                role=USER_ROLE_ADMIN,
                bureau_id=2,
                permissions=[],
            )

    # Service: USER + bureau_id NULL => refus
    def test_service_user_without_bureau_is_rejected(self):
        db = _db_with_bureau_exists()

        with self.assertRaises(HTTPException) as ctx:
            user_service._validate_role_and_bureau(
                db,
                USER_ROLE_USER,
                None,
            )

        self.assertEqual(ctx.exception.status_code, 400)

    # Service: USER + bureau_id renseigne => OK
    def test_service_user_with_bureau_is_allowed(self):
        db = _db_with_bureau_exists()

        user_service._validate_role_and_bureau(
            db,
            USER_ROLE_USER,
            2,
        )

    # Service: ADMIN + bureau_id NULL => OK
    def test_service_admin_without_bureau_is_allowed(self):
        db = _db_with_bureau_exists()

        user_service._validate_role_and_bureau(
            db,
            USER_ROLE_ADMIN,
            None,
        )

    # Service: ADMIN + bureau_id renseigne => refus
    def test_service_admin_with_bureau_is_rejected(self):
        db = _db_with_bureau_exists()

        with self.assertRaises(HTTPException) as ctx:
            user_service._validate_role_and_bureau(
                db,
                USER_ROLE_ADMIN,
                2,
            )

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
