from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.schemas.user_schema import UserCreate
from app.schemas.user_schema import UserPermissionCreate
from app.services.user_service import user_service
from app.security.authorization import has_bureau_access


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _db_with_bureau(exists: bool = True):
    db = MagicMock()
    query = MagicMock()
    query.filter.return_value.first.return_value = (
        SimpleNamespace(id=2, code="BUREAU_2") if exists else None
    )
    db.query.return_value = query
    return db


class TestUserAdminManagement(unittest.TestCase):

    def setUp(self):
        self.db = _db_with_bureau(True)

    # A1. ADMIN peut lire un utilisateur.
    def test_admin_can_read_user(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(10, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ):
            result = user_service.get_by_id(self.db, 10, admin)

        self.assertEqual(result.id, 10)
        self.assertEqual(result.permissions, ["document.read"])

    # A2. ADMIN peut attribuer une permission officielle.
    def test_admin_can_assign_official_permission(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(10, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.user_service.user_repository.update",
            return_value=target,
        ) as mock_update:
            result = user_service.assign_permission(
                self.db,
                10,
                "document.create",
                admin,
            )

        self.assertEqual(result.permissions, ["document.read", "document.create"])
        mock_update.assert_called_once()

    # A3. ADMIN peut retirer une permission.
    def test_admin_can_revoke_permission(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(
            10,
            USER_ROLE_USER,
            permissions=["document.read", "document.create"],
            bureau_id=1,
        )

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.user_service.user_repository.update",
            return_value=target,
        ):
            result = user_service.revoke_permission(
                self.db,
                10,
                "document.create",
                admin,
            )

        self.assertEqual(result.permissions, ["document.read"])

    # A4. ADMIN peut modifier le bureau d'un USER.
    def test_admin_can_update_user_bureau(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(
            10,
            USER_ROLE_USER,
            permissions=["document.read"],
            bureau_id=1,
        )

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.user_service.user_repository.update",
            return_value=target,
        ):
            result = user_service.update_bureau(
                self.db,
                10,
                2,
                admin,
            )

        self.assertEqual(result.bureau_id, 2)
        self.assertEqual(result.permissions, ["document.read"])
        self.assertFalse(has_bureau_access(result, 1))

    # A5. ADMIN conserve l'accès global.
    def test_admin_keeps_global_access(self):
        admin = _user(1, USER_ROLE_ADMIN)
        self.assertTrue(has_bureau_access(admin, 1))
        self.assertTrue(has_bureau_access(admin, 2))

    # B6. Permission inconnue refusée.
    def test_unknown_permission_rejected(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(10, USER_ROLE_USER, permissions=[], bureau_id=1)

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ):
            with self.assertRaises(HTTPException) as ctx:
                user_service.assign_permission(
                    self.db,
                    10,
                    "document.xyz",
                    admin,
                )

        self.assertEqual(ctx.exception.status_code, 400)

    # B7. Permission vide refusée.
    def test_empty_permission_rejected(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(10, USER_ROLE_USER, permissions=[], bureau_id=1)

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ):
            with self.assertRaises(HTTPException) as ctx:
                user_service.assign_permission(
                    self.db,
                    10,
                    "   ",
                    admin,
                )

        self.assertEqual(ctx.exception.status_code, 400)

    # C8. USER ne peut pas modifier ses propres permissions.
    def test_user_cannot_modify_own_permissions(self):
        user = _user(11, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            user_service.assign_permission(
                self.db,
                11,
                "document.create",
                user,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    # C9. USER ne peut pas modifier son propre role.
    def test_user_cannot_modify_own_role(self):
        user = _user(11, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            user_service.update_role(
                self.db,
                11,
                USER_ROLE_ADMIN,
                None,
                user,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    # C10. USER ne peut pas modifier son propre bureau.
    def test_user_cannot_modify_own_bureau(self):
        user = _user(11, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            user_service.update_bureau(
                self.db,
                11,
                2,
                user,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    # C11. USER ne peut pas modifier les permissions d'un autre USER.
    def test_user_cannot_modify_other_user_permissions(self):
        user = _user(11, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            user_service.revoke_permission(
                self.db,
                22,
                "document.read",
                user,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    # C12. USER ne peut pas devenir ADMIN via payload.
    def test_user_cannot_become_admin_via_payload(self):
        user = _user(11, USER_ROLE_USER, permissions=["document.read"], bureau_id=1)
        payload = UserCreate(
            nom="Test",
            prenom="User",
            username="new.user",
            password="secret",
            role=USER_ROLE_ADMIN,
            bureau_id=None,
            permissions=[],
        )

        with self.assertRaises(HTTPException) as ctx:
            user_service.create_by_admin(self.db, payload, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # D13. Les permissions existantes restent intactes après changement de bureau.
    def test_permissions_remain_intact_after_bureau_change(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(
            10,
            USER_ROLE_USER,
            permissions=["document.read", "document.update"],
            bureau_id=1,
        )

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.user_service.user_repository.update",
            return_value=target,
        ):
            result = user_service.update_bureau(
                self.db,
                10,
                2,
                admin,
            )

        self.assertEqual(result.permissions, ["document.read", "document.update"])
        self.assertEqual(result.bureau_id, 2)

    # D14. Le changement de bureau ne donne pas accès à l'ancien bureau.
    def test_bureau_change_does_not_restore_old_access(self):
        admin = _user(1, USER_ROLE_ADMIN)
        target = _user(
            10,
            USER_ROLE_USER,
            permissions=["document.read"],
            bureau_id=1,
        )

        with patch(
            "app.services.user_service.user_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.user_service.user_repository.update",
            return_value=target,
        ):
            result = user_service.update_bureau(
                self.db,
                10,
                2,
                admin,
            )

        self.assertTrue(has_bureau_access(result, 2))
        self.assertFalse(has_bureau_access(result, 1))

    # D15. Le catalogue officiel reste l'unique source de vérité.
    def test_official_catalog_is_single_source_of_truth(self):
        with self.assertRaises(ValidationError):
            UserPermissionCreate(permission="document.xyz")

        with self.assertRaises(ValidationError):
            UserPermissionCreate(permission="   ")


if __name__ == "__main__":
    unittest.main()
