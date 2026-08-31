from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.security.dependencies import get_current_user


class TestUserRouterHttp(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.db = MagicMock()
        bureau_query = MagicMock()
        bureau_query.filter.return_value.first.return_value = SimpleNamespace(
            id=2,
            code="BUREAU_2",
        )
        self.db.query.return_value = bureau_query
        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        app.dependency_overrides.clear()

    def _override_current_user(self, user):
        app.dependency_overrides[get_current_user] = lambda: user

    def _admin_user(self):
        return SimpleNamespace(
            id=1,
            role=USER_ROLE_ADMIN,
            permissions=[],
            bureau_id=None,
            nom="Admin",
            prenom="Root",
            username="admin",
            actif=True,
        )

    def _regular_user(self):
        return SimpleNamespace(
            id=2,
            role=USER_ROLE_USER,
            permissions=[],
            bureau_id=1,
            nom="User",
            prenom="One",
            username="user1",
            actif=True,
        )

    def _user_payload(self, **overrides):
        payload = {
            "nom": "Jean",
            "prenom": "Dupont",
            "username": "jean.dupont",
            "password": "secret123",
            "actif": True,
            "role": USER_ROLE_USER,
            "bureau_id": 2,
            "permissions": ["document.read"],
        }
        payload.update(overrides)
        return payload

    def _api_user(self, user_id=10, permissions=None, bureau_id=1, role=USER_ROLE_USER):
        return SimpleNamespace(
            id=user_id,
            nom="Nom",
            prenom="Prenom",
            username=f"user{user_id}",
            actif=True,
            role=role,
            bureau_id=bureau_id,
            permissions=permissions or [],
        )

    def test_admin_get_users_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = [self._api_user(10, ["document.read"], 1)]

        with patch("app.api.user_router.user_service.get_all", return_value=expected) as mock_get_all:
            response = self.client.get("/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], 10)
        mock_get_all.assert_called_once()

    def test_user_get_users_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.get_all") as mock_get_all:
            response = self.client.get("/users/")

        self.assertEqual(response.status_code, 403)
        mock_get_all.assert_not_called()

    def test_admin_get_user_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(11, ["document.read"], 1)

        with patch("app.api.user_router.user_service.get_by_id", return_value=expected) as mock_get_by_id:
            response = self.client.get("/users/11")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 11)
        mock_get_by_id.assert_called_once()

    def test_user_get_user_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.get_by_id") as mock_get_by_id:
            response = self.client.get("/users/11")

        self.assertEqual(response.status_code, 403)
        mock_get_by_id.assert_not_called()

    def test_admin_post_users_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(20, ["document.read"], 2)

        with patch("app.api.user_router.user_service.create_by_admin", return_value=expected) as mock_create:
            response = self.client.post("/users/", json=self._user_payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 20)
        mock_create.assert_called_once()

    def test_user_post_users_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.create_by_admin") as mock_create:
            response = self.client.post("/users/", json=self._user_payload(role=USER_ROLE_ADMIN))

        self.assertEqual(response.status_code, 403)
        mock_create.assert_not_called()

    def test_admin_post_user_permissions_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(21, ["document.read", "document.create"], 1)

        with patch("app.api.user_router.user_service.assign_permission", return_value=expected) as mock_assign:
            response = self.client.post(
                "/users/21/permissions",
                json={"permission": "document.create"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["permissions"], ["document.read", "document.create"])
        mock_assign.assert_called_once()

    def test_user_post_user_permissions_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.assign_permission") as mock_assign:
            response = self.client.post(
                "/users/21/permissions",
                json={"permission": "document.create"},
            )

        self.assertEqual(response.status_code, 403)
        mock_assign.assert_not_called()

    def test_admin_delete_user_permission_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(22, ["document.read"], 1)

        with patch("app.api.user_router.user_service.revoke_permission", return_value=expected) as mock_revoke:
            response = self.client.delete("/users/22/permissions/document.read")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["permissions"], ["document.read"])
        mock_revoke.assert_called_once()

    def test_user_delete_user_permission_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.revoke_permission") as mock_revoke:
            response = self.client.delete("/users/22/permissions/document.read")

        self.assertEqual(response.status_code, 403)
        mock_revoke.assert_not_called()

    def test_admin_patch_user_bureau_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(23, ["document.read", "document.update"], 2)

        with patch("app.api.user_router.user_service.update_bureau", return_value=expected) as mock_update_bureau:
            response = self.client.patch(
                "/users/23/bureau",
                json={"bureau_id": 2},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bureau_id"], 2)
        self.assertEqual(response.json()["permissions"], ["document.read", "document.update"])
        mock_update_bureau.assert_called_once()

    def test_user_patch_user_bureau_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.update_bureau") as mock_update_bureau:
            response = self.client.patch(
                "/users/23/bureau",
                json={"bureau_id": 2},
            )

        self.assertEqual(response.status_code, 403)
        mock_update_bureau.assert_not_called()

    def test_admin_patch_user_role_authorized(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(24, ["document.read"], None, role=USER_ROLE_ADMIN)

        with patch("app.api.user_router.user_service.update_role", return_value=expected) as mock_update_role:
            response = self.client.patch(
                "/users/24/role",
                json={"role": "ADMIN"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "ADMIN")
        mock_update_role.assert_called_once()

    def test_user_patch_user_role_forbidden(self):
        user = self._regular_user()
        self._override_current_user(user)

        with patch("app.api.user_router.user_service.update_role") as mock_update_role:
            response = self.client.patch(
                "/users/24/role",
                json={"role": "ADMIN"},
            )

        self.assertEqual(response.status_code, 403)
        mock_update_role.assert_not_called()

    def test_user_cannot_become_admin_via_payload(self):
        user = self._regular_user()
        self._override_current_user(user)

        response = self.client.post(
            "/users/",
            json=self._user_payload(role=USER_ROLE_ADMIN),
        )

        self.assertEqual(response.status_code, 403)

    def test_unknown_permission_is_rejected(self):
        admin = self._admin_user()
        self._override_current_user(admin)

        response = self.client.post(
            "/users/21/permissions",
            json={"permission": "document.xyz"},
        )

        self.assertEqual(response.status_code, 422)

    def test_empty_permission_is_rejected(self):
        admin = self._admin_user()
        self._override_current_user(admin)

        response = self.client.post(
            "/users/21/permissions",
            json={"permission": "   "},
        )

        self.assertEqual(response.status_code, 422)

    def test_permissions_remain_intact_when_bureau_changes(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(30, ["document.read", "document.update"], 2)

        with patch("app.api.user_router.user_service.update_bureau", return_value=expected):
            response = self.client.patch(
                "/users/30/bureau",
                json={"bureau_id": 2},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["permissions"], ["document.read", "document.update"])
        self.assertEqual(response.json()["bureau_id"], 2)

    def test_bureau_control_remains_strict(self):
        user = self._regular_user()
        self._override_current_user(user)

        response = self.client.get("/users/")

        self.assertEqual(response.status_code, 403)

    def test_routes_use_service_layer(self):
        admin = self._admin_user()
        self._override_current_user(admin)
        expected = self._api_user(40, ["document.read"], 1)

        with patch("app.api.user_router.user_service.get_by_id", return_value=expected) as mock_get_by_id:
            response = self.client.get("/users/40")

        self.assertEqual(response.status_code, 200)
        mock_get_by_id.assert_called_once()


if __name__ == "__main__":
    unittest.main()
