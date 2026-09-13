from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER
from app.security.dependencies import get_current_user
from app.services.auth_service import auth_service


class TestAuthMe(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        app.dependency_overrides.clear()

    def _override_current_user(self, user):
        app.dependency_overrides[get_current_user] = lambda: user

    def _profile(self, username, bureau, circonscription, user_id):
        return {
            "id": user_id,
            "nom": "Nom",
            "prenom": "Prenom",
            "username": username,
            "actif": True,
            "role": USER_ROLE_USER,
            "bureau": {
                "id": user_id,
                "nom": bureau,
            },
            "circonscription": {
                "id": 1,
                "nom": circonscription,
            },
            "permissions": ["document.read"],
        }

    def test_user_profiles_return_their_own_bureau_and_circonscription(self):
        profiles = (
            ("ackim", "ENREGISTREMENT"),
            ("mutombo", "DOMAINE_NOTARIAT"),
            ("junior", "DOCUMENTATION_ARCHIVES"),
            ("kenny", "CONTENTIEUX"),
        )

        for user_id, (username, bureau) in enumerate(profiles, start=2):
            with self.subTest(username=username):
                current_user = SimpleNamespace(id=user_id)
                self._override_current_user(current_user)
                profile = self._profile(
                    username,
                    bureau,
                    "Gombe",
                    user_id,
                )

                with patch.object(
                    auth_service,
                    "get_current_user_profile",
                    return_value=profile,
                ):
                    response = self.client.get("/auth/me")

                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["username"], username)
                self.assertEqual(body["bureau"]["nom"], bureau)
                self.assertEqual(
                    body["circonscription"]["nom"],
                    "Gombe",
                )

    def test_admin_profile_has_no_bureau_and_has_admin_circonscription(self):
        current_user = SimpleNamespace(id=1)
        self._override_current_user(current_user)
        profile = {
            "id": 1,
            "nom": "Manager",
            "prenom": "Sia",
            "username": "sia.manager",
            "actif": True,
            "role": USER_ROLE_ADMIN,
            "bureau": None,
            "circonscription": {
                "id": 1,
                "nom": "Gombe",
            },
            "permissions": [],
        }

        with patch.object(
            auth_service,
            "get_current_user_profile",
            return_value=profile,
        ):
            response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["bureau"])
        self.assertEqual(
            response.json()["circonscription"]["nom"],
            "Gombe",
        )

    def test_profile_does_not_expose_sensitive_fields(self):
        current_user = SimpleNamespace(id=2)
        self._override_current_user(current_user)
        profile = self._profile(
            "ackim",
            "ENREGISTREMENT",
            "Gombe",
            2,
        )

        with patch.object(
            auth_service,
            "get_current_user_profile",
            return_value=profile,
        ):
            response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.json())
        self.assertNotIn("bureau_id", response.json())
        self.assertNotIn("admin_circonscription_id", response.json())

    def test_service_derives_user_profile_from_authenticated_user_relations(self):
        circonscription = SimpleNamespace(id=1, nom="Gombe")
        bureau = SimpleNamespace(
            id=2,
            nom="ENREGISTREMENT",
            circonscription=circonscription,
        )
        loaded_user = SimpleNamespace(
            id=2,
            nom="Nom",
            prenom="Prenom",
            username="ackim",
            actif=True,
            role=USER_ROLE_USER,
            permissions=["document.read"],
            bureau=bureau,
            admin_circonscription=None,
        )
        db = MagicMock()
        (
            db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value
        ) = loaded_user

        profile = auth_service.get_current_user_profile(
            db,
            SimpleNamespace(id=2),
        )

        self.assertEqual(profile["bureau"], {
            "id": 2,
            "nom": "ENREGISTREMENT",
        })
        self.assertEqual(profile["circonscription"], {
            "id": 1,
            "nom": "Gombe",
        })
        self.assertNotIn("password", profile)

    def test_service_uses_admin_circonscription_and_no_bureau(self):
        admin_circonscription = SimpleNamespace(id=1, nom="Gombe")
        loaded_admin = SimpleNamespace(
            id=1,
            nom="Manager",
            prenom="Sia",
            username="sia.manager",
            actif=True,
            role=USER_ROLE_ADMIN,
            permissions=[],
            bureau=None,
            admin_circonscription=admin_circonscription,
        )
        db = MagicMock()
        (
            db.query.return_value
            .options.return_value
            .filter.return_value
            .first.return_value
        ) = loaded_admin

        profile = auth_service.get_current_user_profile(
            db,
            SimpleNamespace(id=1),
        )

        self.assertIsNone(profile["bureau"])
        self.assertEqual(profile["circonscription"]["nom"], "Gombe")


if __name__ == "__main__":
    unittest.main()
