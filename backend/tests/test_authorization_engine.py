from types import SimpleNamespace
import unittest

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.security.authorization import has_bureau_access
from app.security.authorization import has_permission
from app.security.authorization import is_admin
from app.security.authorization import require_permission
from app.security.dependencies import get_current_user


def _make_user(role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        role=role,
        permissions=permissions,
        bureau_id=bureau_id,
    )


class TestAuthorizationEngine(unittest.TestCase):

    def test_admin_is_recognized(self):
        admin = _make_user(USER_ROLE_ADMIN, permissions=[], bureau_id=None)
        self.assertTrue(is_admin(admin))

    def test_user_is_not_admin(self):
        user = _make_user(USER_ROLE_USER, permissions=[], bureau_id=2)
        self.assertFalse(is_admin(user))

    def test_user_with_document_create_permission(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.create"], bureau_id=2)
        self.assertTrue(has_permission(user, "document.create"))

    def test_user_without_document_delete_permission(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.read"], bureau_id=2)
        self.assertFalse(has_permission(user, "document.delete"))

    def test_unknown_permission_is_rejected(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.xyz"], bureau_id=2)
        self.assertFalse(has_permission(user, "document.xyz"))

    def test_empty_permission_is_rejected(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.create"], bureau_id=2)
        self.assertFalse(has_permission(user, ""))

    def test_user_has_access_to_own_bureau(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.read"], bureau_id=2)
        self.assertTrue(has_bureau_access(user, 2))

    def test_user_has_no_access_to_other_bureau(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.read"], bureau_id=2)
        self.assertFalse(has_bureau_access(user, 1))

    def test_user_without_bureau_has_no_access(self):
        user = _make_user(USER_ROLE_USER, permissions=["document.read"], bureau_id=None)
        self.assertFalse(has_bureau_access(user, 1))

    def test_admin_has_global_bureau_access_first_case(self):
        admin = _make_user(USER_ROLE_ADMIN, permissions=[], bureau_id=None)
        self.assertTrue(has_bureau_access(admin, 1))

    def test_admin_has_global_bureau_access_second_case(self):
        admin = _make_user(USER_ROLE_ADMIN, permissions=[], bureau_id=None)
        self.assertTrue(has_bureau_access(admin, 4))

    def test_require_permission_distinguishes_401_and_403(self):
        app = FastAPI()

        @app.get("/check")
        async def check_permission(_user=Depends(require_permission("document.create"))):
            return {"ok": True}

        client = TestClient(app)

        def unauthenticated_override():
            raise HTTPException(status_code=401, detail="Token invalide")

        app.dependency_overrides[get_current_user] = unauthenticated_override
        response_401 = client.get("/check")
        self.assertEqual(response_401.status_code, 401)

        def authenticated_without_permission_override():
            return _make_user(
                USER_ROLE_USER,
                permissions=["document.read"],
                bureau_id=2,
            )

        app.dependency_overrides[get_current_user] = authenticated_without_permission_override
        response_403 = client.get("/check")
        self.assertEqual(response_403.status_code, 403)


if __name__ == "__main__":
    unittest.main()
