from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER
from app.schemas.bureau_schema import BureauCreate, BureauUpdate
from app.services.bureau_service import STANDARD_BUREAUX, bureau_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None, admin_circonscription_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
        admin_circonscription_id=admin_circonscription_id,
    )


def _bureau(bureau_id: int, circonscription_id: int = 1, code="CONTENTIEUX"):
    return SimpleNamespace(
        id=bureau_id,
        circonscription_id=circonscription_id,
        code=code,
        nom=code.title(),
        description=None,
        actif=True,
    )


def _approved_request(user_id: int, bureau_id: int, expired=False):
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission="bureau.read",
        status="APPROVED",
        document_id=None,
        expires_at=datetime.now(timezone.utc) + timedelta(
            minutes=-5 if expired else 10
        ),
    )


class TestBureauRbac(unittest.TestCase):

    def test_standard_bureaux_are_defined_once(self):
        self.assertEqual(
            tuple(code for code, _ in STANDARD_BUREAUX),
            (
                "CONTENTIEUX",
                "ENREGISTREMENT",
                "DOMAINE_NOTARIAT",
                "DOCUMENTATION_ARCHIVES",
            ),
        )

    def test_admin_can_list_all_bureaux(self):
        db = SimpleNamespace()
        # ADMIN sans circonscription assignee -> comportement historique global.
        admin = _user(1, USER_ROLE_ADMIN)
        expected = [_bureau(1), _bureau(2, code="ENREGISTREMENT")]

        with patch(
            "app.services.bureau_service.bureau_repository.get_all",
            return_value=expected,
        ) as get_all:
            result = bureau_service.get_all(db, admin)

        self.assertEqual(result, expected)
        get_all.assert_called_once_with(db)

    def test_user_can_list_only_own_gombe_bureau(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["bureau.read"], bureau_id=1)
        # Le bureau 1 appartient a la circonscription 1 (Gombe).
        bureau = _bureau(1, circonscription_id=1)
        bureaux_circonscription = [
            _bureau(1, circonscription_id=1),
            _bureau(2, circonscription_id=1, code="ENREGISTREMENT"),
        ]

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=bureau,
        ) as get_by_id, patch(
            "app.services.bureau_service.bureau_repository.get_active_by_circonscription",
            return_value=bureaux_circonscription,
        ) as get_scoped:
            result = bureau_service.get_all(db, user)

        # Le USER recoit desormais les bureaux actifs de SA circonscription.
        self.assertEqual(result, bureaux_circonscription)
        get_by_id.assert_called_once_with(db, 1)
        get_scoped.assert_called_once_with(db, 1)

    def test_user_cannot_read_another_gombe_bureau(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["bureau.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as context:
            bureau_service.get_by_id(db, 2, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_user_without_bureau_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["bureau.read"])

        with self.assertRaises(HTTPException) as context:
            bureau_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_user_without_bureau_read_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ), self.assertRaises(HTTPException) as context:
            bureau_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_unknown_bureau_returns_404_for_admin(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN)

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=None,
        ), self.assertRaises(HTTPException) as context:
            bureau_service.get_by_id(db, 99, admin)

        self.assertEqual(context.exception.status_code, 404)

    def test_valid_temporary_bureau_read_is_limited_to_own_bureau(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)
        bureau = _bureau(1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 1),
        ), patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=bureau,
        ):
            result = bureau_service.get_by_id(db, 1, user)

        self.assertEqual(result, bureau)

    def test_temporary_permission_for_other_bureau_is_forbidden(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 2),
        ), self.assertRaises(HTTPException) as context:
            bureau_service.get_all(db, user)

        self.assertEqual(context.exception.status_code, 403)

    def test_admin_can_create_bureau_in_existing_circonscription(self):
        admin = _user(1, USER_ROLE_ADMIN)
        circonscription_query = MagicMock()
        circonscription_query.filter.return_value.first.return_value = SimpleNamespace(id=2)
        db = MagicMock(query=MagicMock(return_value=circonscription_query))
        data = BureauCreate(code="CONTENTIEUX", nom="Contentieux", circonscription_id=2)

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_code",
            return_value=None,
        ), patch(
            "app.services.bureau_service.bureau_repository.get_by_name",
            return_value=None,
        ), patch(
            "app.services.bureau_service.bureau_repository.create",
            side_effect=lambda _, bureau: bureau,
        ):
            result = bureau_service.create(db, data, admin)

        self.assertEqual(result.circonscription_id, 2)

    def test_user_cannot_create_update_or_disable_bureau(self):
        db = SimpleNamespace()
        user = _user(
            2,
            USER_ROLE_USER,
            ["bureau.create", "bureau.update", "bureau.disable"],
            bureau_id=1,
        )
        create_data = BureauCreate(code="NOUVEAU", nom="Nouveau", circonscription_id=1)

        for operation, arguments in (
            (bureau_service.create, (db, create_data, user)),
            (bureau_service.update, (db, 1, BureauUpdate(nom="Nouveau"), user)),
            (bureau_service.disable, (db, 1, user)),
        ):
            with self.subTest(operation=operation.__name__), self.assertRaises(HTTPException) as context:
                operation(*arguments)
            self.assertEqual(context.exception.status_code, 403)

    def test_admin_can_update_without_moving_circonscription(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN)
        bureau = _bureau(1, circonscription_id=1)

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.bureau_service.bureau_repository.update",
            return_value=bureau,
        ):
            result = bureau_service.update(db, 1, BureauUpdate(description="Mise a jour"), admin)

        self.assertEqual(result.circonscription_id, 1)
        self.assertEqual(result.description, "Mise a jour")

    def test_admin_can_disable_without_deleting_bureau(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN)
        bureau = _bureau(1)

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.bureau_service.bureau_repository.update",
            return_value=bureau,
        ) as update:
            result = bureau_service.disable(db, 1, admin)

        self.assertFalse(result.actif)
        update.assert_called_once_with(db, bureau)

    # TEST 21
    def test_user_get_all_returns_bureaux_of_his_circonscription(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["bureau.read"], bureau_id=1)
        own_bureau = _bureau(1, circonscription_id=1)
        bureaux_gombe = [
            _bureau(1, circonscription_id=1),
            _bureau(2, circonscription_id=1, code="ENREGISTREMENT"),
            _bureau(3, circonscription_id=1, code="DOMAINE_NOTARIAT"),
            _bureau(4, circonscription_id=1, code="DOCUMENTATION_ARCHIVES"),
        ]

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=own_bureau,
        ), patch(
            "app.services.bureau_service.bureau_repository.get_active_by_circonscription",
            return_value=bureaux_gombe,
        ) as get_scoped:
            result = bureau_service.get_all(db, user)

        self.assertEqual(len(result), 4)
        get_scoped.assert_called_once_with(db, 1)

    # TEST 22
    def test_user_get_all_never_returns_other_circonscription_bureau(self):
        db = SimpleNamespace()
        user = _user(2, USER_ROLE_USER, ["bureau.read"], bureau_id=1)
        own_bureau = _bureau(1, circonscription_id=1)
        # Le repository scoped ne retourne QUE la circonscription 1.
        bureaux_gombe = [_bureau(1, circonscription_id=1)]

        with patch(
            "app.services.bureau_service.bureau_repository.get_by_id",
            return_value=own_bureau,
        ), patch(
            "app.services.bureau_service.bureau_repository.get_active_by_circonscription",
            return_value=bureaux_gombe,
        ) as get_scoped:
            result = bureau_service.get_all(db, user)

        self.assertTrue(all(b.circonscription_id == 1 for b in result))
        # L'appel est bien borne a la circonscription du USER (1), jamais 2.
        get_scoped.assert_called_once_with(db, 1)

    # TEST 23
    def test_admin_get_all_returns_bureaux_of_his_circonscription(self):
        db = SimpleNamespace()
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        bureaux_gombe = [
            _bureau(1, circonscription_id=1),
            _bureau(2, circonscription_id=1, code="ENREGISTREMENT"),
        ]

        with patch(
            "app.services.bureau_service.bureau_repository.get_active_by_circonscription",
            return_value=bureaux_gombe,
        ) as get_scoped:
            result = bureau_service.get_all(db, admin)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(b.circonscription_id == 1 for b in result))
        get_scoped.assert_called_once_with(db, 1)