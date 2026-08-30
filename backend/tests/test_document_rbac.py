from datetime import date
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.schemas.document_schema import DocumentCreate
from app.schemas.document_schema import DocumentUpdate
from app.services.document_service import document_service


def _user(user_id: int, role: str, permissions, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions,
        bureau_id=bureau_id,
    )


def _doc(doc_id: int, bureau_id: int, nom_document: str = "Doc"):
    return SimpleNamespace(
        id=doc_id,
        bureau_id=bureau_id,
        nom_document=nom_document,
    )


class TestDocumentRbac(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
        )

    # TEST 1
    def test_admin_document_read_can_see_bureau_1_document(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.read"])
        expected = _doc(1, 1)

        with patch("app.services.document_service.document_repository.get_by_id", return_value=expected):
            result = document_service.get_by_id(self.db, 1, admin)

        self.assertEqual(result.bureau_id, 1)

    # TEST 2
    def test_admin_document_read_can_see_bureau_2_document(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.read"])
        expected = _doc(2, 2)

        with patch("app.services.document_service.document_repository.get_by_id", return_value=expected):
            result = document_service.get_by_id(self.db, 2, admin)

        self.assertEqual(result.bureau_id, 2)

    # TEST 3
    def test_user_bureau_1_document_read_can_see_own_document(self):
        user = _user(11, USER_ROLE_USER, ["document.read"], bureau_id=1)
        expected = _doc(3, 1)

        with patch("app.services.document_service.document_repository.get_by_id", return_value=expected) as mock_get_by_id:
            result = document_service.get_by_id(self.db, 3, user)

        self.assertEqual(result.bureau_id, 1)
        mock_get_by_id.assert_called_once_with(self.db, 3, bureau_id=1)

    # TEST 4
    def test_user_bureau_1_document_read_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["document.read"], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[None, _doc(4, 2)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.get_by_id(self.db, 4, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 5
    def test_user_bureau_1_without_document_read_is_403(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            document_service.get_by_id(self.db, 5, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 6
    def test_user_bureau_1_document_update_own_document_allowed(self):
        user = _user(11, USER_ROLE_USER, ["document.update"], bureau_id=1)
        target_doc = _doc(6, 1, nom_document="Avant")

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[target_doc, target_doc],
        ) as mock_get_by_id, patch(
            "app.services.document_service.document_repository.update",
            return_value=target_doc,
        ), patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.document_field_value_repository.get_by_document_id",
            return_value=[],
        ), patch(
            "app.services.document_service.document_field_repository.get_by_ids",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ):
            payload = DocumentUpdate(nom_document="Apres")
            result = document_service.update(self.db, 6, payload, user)

        self.assertEqual(result.id, 6)
        self.assertEqual(target_doc.nom_document, "Apres")
        mock_get_by_id.assert_any_call(self.db, 6, bureau_id=1)

    # TEST 7
    def test_user_bureau_1_document_update_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["document.update"], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[None, _doc(7, 2)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.update(
                    self.db,
                    7,
                    DocumentUpdate(nom_document="Interdit"),
                    user,
                )

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 8
    def test_user_bureau_1_document_delete_own_document_allowed(self):
        user = _user(11, USER_ROLE_USER, ["document.delete"], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=_doc(8, 1),
        ) as mock_get_by_id, patch(
            "app.services.document_service.document_repository.delete",
            return_value=True,
        ) as mock_delete:
            result = document_service.delete(self.db, 8, user)

        self.assertTrue(result)
        mock_get_by_id.assert_called_once_with(self.db, 8, bureau_id=1)
        mock_delete.assert_called_once()

    # TEST 9
    def test_user_bureau_1_document_delete_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["document.delete"], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[None, _doc(9, 2)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.delete(self.db, 9, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 10
    def test_user_bureau_1_document_create_assigned_to_bureau_1(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)

        payload = DocumentCreate(
            reference_archive="REF-10",
            nom_document="Nouveau",
            date_creation=date(2026, 8, 30),
            type_document_id=1,
        )

        created_doc = _doc(10, 1)

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            result = document_service.create(self.db, payload, user)

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.encodeur_id, 11)
        self.assertEqual(result.bureau_id, 1)

    # TEST 11
    def test_user_bureau_1_document_create_other_bureau_attempt_is_ignored(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)

        payload = DocumentCreate.model_validate(
            {
                "reference_archive": "REF-11",
                "nom_document": "Nouveau 2",
                "date_creation": "2026-08-30",
                "type_document_id": 1,
                "bureau_id": 999,
            }
        )

        created_doc = _doc(11, 1)

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            document_service.create(self.db, payload, user)

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)

    # TEST 12
    def test_admin_list_includes_documents_from_multiple_bureaux(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.read"])
        docs = [_doc(12, 1), _doc(13, 2), _doc(14, 3), _doc(15, 4)]

        with patch("app.services.document_service.document_repository.get_all", return_value=docs) as mock_get_all:
            result = document_service.get_all(self.db, admin)

        self.assertEqual(len(result), 4)
        self.assertEqual({item.bureau_id for item in result}, {1, 2, 3, 4})
        mock_get_all.assert_called_once_with(self.db, bureau_id=None)

    # TEST 13
    def test_user_bureau_2_list_contains_only_bureau_2_documents(self):
        user = _user(12, USER_ROLE_USER, ["document.read"], bureau_id=2)
        docs = [_doc(16, 2), _doc(17, 2)]

        with patch("app.services.document_service.document_repository.get_all", return_value=docs) as mock_get_all:
            result = document_service.get_all(self.db, user)

        self.assertTrue(all(item.bureau_id == 2 for item in result))
        mock_get_all.assert_called_once_with(self.db, bureau_id=2)

    # TEST 14
    def test_user_bureau_2_search_returns_only_bureau_2_documents(self):
        user = _user(12, USER_ROLE_USER, ["document.read"], bureau_id=2)
        docs = [_doc(18, 2), _doc(19, 2)]

        with patch("app.services.document_service.document_repository.search", return_value=docs) as mock_search:
            result = document_service.search(
                db=self.db,
                current_user=user,
                reference_archive="REF",
                nom_document="Nom",
                code_foncier="CF",
                numero_ordre="N1",
                type_document_id=1,
                phase_id=2,
                circonscription_id=3,
                date_debut=date(2026, 1, 1),
                date_fin=date(2026, 12, 31),
            )

        self.assertTrue(all(item.bureau_id == 2 for item in result))
        mock_search.assert_called_once_with(
            db=self.db,
            bureau_id=2,
            reference_archive="REF",
            nom_document="Nom",
            code_foncier="CF",
            numero_ordre="N1",
            type_document_id=1,
            phase_id=2,
            circonscription_id=3,
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 12, 31),
        )


if __name__ == "__main__":
    unittest.main()
