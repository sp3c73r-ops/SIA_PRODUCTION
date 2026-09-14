from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import ANY, MagicMock, patch

from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.schemas.document_schema import DocumentCreate
from app.schemas.document_schema import DocumentUpdate
from app.services.attachment_service import attachment_service
from app.services.document_service import document_service


def _user(user_id: int, role: str, permissions, bureau_id=None, admin_circonscription_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions,
        bureau_id=bureau_id,
        admin_circonscription_id=admin_circonscription_id,
    )


def _doc(doc_id: int, bureau_id: int, nom_document: str = "Doc"):
    return SimpleNamespace(
        id=doc_id,
        bureau_id=bureau_id,
        nom_document=nom_document,
    )


def _initial_file():
    return UploadFile(
        filename="initial.pdf",
        file=BytesIO(b"initial content"),
    )


class TestDocumentRbac(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=MagicMock(),
            rollback=MagicMock(),
            flush=MagicMock(),
            add=MagicMock(),
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

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
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
    def test_user_with_document_delete_cannot_delete_document(self):
        user = _user(11, USER_ROLE_USER, ["document.delete"], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=_doc(8, 1),
        ) as mock_get_by_id, patch(
            "app.services.document_service.document_repository.delete",
            return_value=True,
        ) as mock_delete:
            with self.assertRaises(HTTPException) as ctx:
                document_service.delete(self.db, 8, user)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_get_by_id.assert_not_called()
        mock_delete.assert_not_called()

    # TEST 9
    def test_user_without_document_delete_cannot_delete_document(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=_doc(9, 1),
        ) as mock_get_by_id, patch(
            "app.services.document_service.document_repository.delete",
        ) as mock_delete:
            with self.assertRaises(HTTPException) as ctx:
                document_service.delete(self.db, 9, user)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_get_by_id.assert_not_called()
        mock_delete.assert_not_called()

    # TEST 10
    def test_admin_can_delete_document_in_own_circonscription(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.delete"], admin_circonscription_id=5)
        target = _doc(10, 1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=target,
        ) as mock_get_by_id, patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.delete",
            side_effect=lambda _db, document: setattr(document, "is_deleted", True) or True,
        ) as mock_delete:
            result = document_service.delete(self.db, 10, admin)

        self.assertTrue(result)
        self.assertTrue(target.is_deleted)
        mock_get_by_id.assert_called_once_with(self.db, 10)
        mock_delete.assert_called_once_with(self.db, target)

    def test_admin_from_other_circonscription_cannot_delete_document(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.delete"], admin_circonscription_id=6)

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(id=1, circonscription_id=5),
        ), patch(
            "app.services.document_service.document_repository.delete",
        ) as mock_delete:
            with self.assertRaises(HTTPException) as ctx:
                document_service.delete(self.db, 10, admin)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_delete.assert_not_called()

    def test_admin_delete_already_deleted_document_keeps_existing_behavior(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.delete"], admin_circonscription_id=5)
        target = _doc(10, 1)
        target.is_deleted = True

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=target,
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(id=1, circonscription_id=5),
        ), patch(
            "app.services.document_service.document_repository.delete",
            return_value=True,
        ) as mock_delete:
            result = document_service.delete(self.db, 10, admin)

        self.assertTrue(result)
        self.assertTrue(target.is_deleted)
        mock_delete.assert_called_once_with(self.db, target)

    # TEST 11
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
        ), patch.object(
            attachment_service,
            "create",
            return_value=SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(
                id=1,
                circonscription_id=5,
            ),
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            result = document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.encodeur_id, 11)
        self.assertEqual(created_document_arg.circonscription_id, 5)
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
        ), patch.object(
            attachment_service,
            "create",
            return_value=SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(
                id=1,
                circonscription_id=5,
            ),
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.circonscription_id, 5)

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
            scope_circonscription_id=None,
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 12, 31),
        )

    # TEST 14b
    def test_admin_search_is_scoped_to_his_circonscription(self):
        admin = _user(
            100,
            USER_ROLE_ADMIN,
            ["document.read"],
            admin_circonscription_id=1,
        )
        docs = [_doc(30, 1), _doc(31, 2)]

        with patch("app.services.document_service.document_repository.search", return_value=docs) as mock_search:
            document_service.search(
                db=self.db,
                current_user=admin,
                reference_archive="REF",
            )

        mock_search.assert_called_once_with(
            db=self.db,
            bureau_id=None,
            reference_archive="REF",
            nom_document=None,
            code_foncier=None,
            numero_ordre=None,
            type_document_id=None,
            phase_id=None,
            circonscription_id=None,
            scope_circonscription_id=1,
            date_debut=None,
            date_fin=None,
        )

    # TEST 14c
    def test_admin_search_combines_client_filter_and_scope(self):
        admin = _user(
            100,
            USER_ROLE_ADMIN,
            ["document.read"],
            admin_circonscription_id=1,
        )

        with patch("app.services.document_service.document_repository.search", return_value=[]) as mock_search:
            document_service.search(
                db=self.db,
                current_user=admin,
                circonscription_id=9,
            )

        mock_search.assert_called_once_with(
            db=self.db,
            bureau_id=None,
            reference_archive=None,
            nom_document=None,
            code_foncier=None,
            numero_ordre=None,
            type_document_id=None,
            phase_id=None,
            circonscription_id=9,
            scope_circonscription_id=1,
            date_debut=None,
            date_fin=None,
        )

    # TEST 14d
    def test_admin_sans_circonscription_search_reste_inchange(self):
        admin = _user(100, USER_ROLE_ADMIN, ["document.read"])

        with patch("app.services.document_service.document_repository.search", return_value=[]) as mock_search:
            document_service.search(
                db=self.db,
                current_user=admin,
            )

        mock_search.assert_called_once_with(
            db=self.db,
            bureau_id=None,
            reference_archive=None,
            nom_document=None,
            code_foncier=None,
            numero_ordre=None,
            type_document_id=None,
            phase_id=None,
            circonscription_id=None,
            scope_circonscription_id=None,
            date_debut=None,
            date_fin=None,
        )

    # TEST 15
    def test_user_bureau_1_create_sans_circonscription_derivee_du_bureau(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)

        payload = DocumentCreate(
            reference_archive="REF-15",
            nom_document="Sans circonscription",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )

        created_doc = _doc(15, 1)

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            return_value=SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ) as mock_bureau, patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.encodeur_id, 11)
        self.assertEqual(created_document_arg.circonscription_id, 5)
        mock_bureau.assert_called_once_with(self.db, 1)

    # TEST 16
    def test_user_bureau_1_create_circonscription_zero_payload_ignoree(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)

        payload = DocumentCreate(
            reference_archive="REF-16",
            nom_document="Circonscription zero",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
            circonscription_id=0,
        )

        created_doc = _doc(16, 1)

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            return_value=SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            result = document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.encodeur_id, 11)
        self.assertEqual(created_document_arg.circonscription_id, 5)
        self.assertEqual(result.bureau_id, 1)

    # TEST 17
    def test_user_bureau_1_create_autre_circonscription_payload_ignoree(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)

        payload = DocumentCreate(
            reference_archive="REF-17",
            nom_document="Autre circonscription",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
            circonscription_id=999,
        )

        created_doc = _doc(17, 1)

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            return_value=SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        created_document_arg = mock_create.call_args.args[1]
        self.assertEqual(created_document_arg.bureau_id, 1)
        self.assertEqual(created_document_arg.circonscription_id, 5)

    def test_user_create_document_with_initial_attachment(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-INITIAL",
            nom_document="Avec piece initiale",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        created_doc = _doc(30, 1)
        created_attachment = SimpleNamespace(
            chemin_fichier="missing-in-test.pdf",
        )

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=created_doc,
        ) as mock_create, patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            return_value=created_attachment,
        ) as mock_attachment, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=created_doc,
        ):
            result = document_service.create(
                self.db,
                payload,
                user,
                initial_file=_initial_file(),
            )

        self.assertEqual(result.id, 30)
        mock_create.assert_called_once_with(
            self.db,
            mock_create.call_args.args[1],
            commit=False,
        )
        mock_attachment.assert_called_once_with(
            self.db,
            30,
            mock_attachment.call_args.args[2],
            user,
            check_permission=False,
            commit=False,
            created_paths=ANY,
        )
        self.db.commit.assert_called_once()

    def test_user_create_document_with_multiple_initial_attachments(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-MULTI-INITIAL",
            nom_document="Avec plusieurs pieces initiales",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        files = [
            _initial_file(),
            UploadFile(filename="second.pdf", file=BytesIO(b"second")),
            UploadFile(filename="third.pdf", file=BytesIO(b"third")),
        ]

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=_doc(32, 1),
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            side_effect=lambda *args, **kwargs: SimpleNamespace(
                chemin_fichier="missing-in-test.pdf",
            ),
        ) as mock_attachment, patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=_doc(32, 1),
        ):
            result = document_service.create(
                self.db,
                payload,
                user,
                initial_files=files,
            )

        self.assertEqual(result.id, 32)
        self.assertEqual(mock_attachment.call_count, 3)
        self.assertEqual(
            [call.args[2] for call in mock_attachment.call_args_list],
            files,
        )
        for call in mock_attachment.call_args_list:
            self.assertEqual(call.kwargs["check_permission"], False)
            self.assertEqual(call.kwargs["commit"], False)
        self.db.commit.assert_called_once()

    def test_intermediate_initial_attachment_failure_rolls_back_and_cleans_files(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-MULTI-ROLLBACK",
            nom_document="Echec piece intermediaire",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        first_path = self._temporary_path("initial-first.pdf")
        first_path.write_bytes(b"first")
        created_paths = []

        def create_attachment(*args, **kwargs):
            if not created_paths:
                kwargs["created_paths"].append(first_path)
                created_paths.append(first_path)
                return SimpleNamespace(chemin_fichier=str(first_path))
            raise RuntimeError("second attachment failure")

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=_doc(33, 1),
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            side_effect=create_attachment,
        ):
            with self.assertRaises(RuntimeError):
                document_service.create(
                    self.db,
                    payload,
                    user,
                    initial_files=[
                        _initial_file(),
                        UploadFile(
                            filename="second.pdf",
                            file=BytesIO(b"second"),
                        ),
                    ],
                )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()
        self.assertFalse(first_path.exists())

    def _temporary_path(self, filename):
        import tempfile

        path = Path(tempfile.gettempdir()) / filename
        if path.exists():
            path.unlink()
        self.addCleanup(lambda: path.unlink() if path.exists() else None)
        return path

    def test_user_cannot_create_document_without_initial_attachment(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        payload = DocumentCreate(
            reference_archive="REF-NO-INITIAL",
            nom_document="Sans piece initiale",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )

        with patch(
            "app.services.document_service.document_repository.create",
        ) as mock_create:
            with self.assertRaises(HTTPException) as ctx:
                document_service.create(self.db, payload, user)

        self.assertEqual(ctx.exception.status_code, 400)
        mock_create.assert_not_called()

    def test_initial_attachment_failure_rolls_back_document_creation(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-ROLLBACK",
            nom_document="Echec piece initiale",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=_doc(31, 1),
        ) as mock_create, patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            side_effect=RuntimeError("attachment failure"),
        ):
            with self.assertRaises(RuntimeError):
                document_service.create(
                    self.db,
                    payload,
                    user,
                    initial_file=_initial_file(),
                )

        self.assertEqual(mock_create.call_args.kwargs["commit"], False)
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_duplicate_reference_archive_returns_409_after_rollback(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-DUPLICATE",
            nom_document="Reference dupliquee",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        duplicate_error = IntegrityError(
            "insert",
            {},
            SimpleNamespace(
                sqlstate="23505",
                diag=SimpleNamespace(
                    constraint_name="documents_reference_archive_key",
                ),
            ),
        )

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            side_effect=duplicate_error,
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.create(
                    self.db,
                    payload,
                    user,
                    initial_file=_initial_file(),
                )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(
            ctx.exception.detail,
            "Cette référence d'archive existe déjà.",
        )
        self.db.rollback.assert_called_once()

    def test_duplicate_reference_archive_cleans_multiple_created_files(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-DUPLICATE-MULTI",
            nom_document="Reference dupliquee avec pieces",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        created_paths = [
            self._temporary_path("duplicate-first.pdf"),
            self._temporary_path("duplicate-second.pdf"),
        ]
        for path in created_paths:
            path.write_bytes(b"temporary attachment")
        duplicate_error = IntegrityError(
            "commit",
            {},
            SimpleNamespace(
                sqlstate="23505",
                diag=SimpleNamespace(
                    constraint_name="documents_reference_archive_key",
                ),
            ),
        )

        def create_attachment(*args, **kwargs):
            path = created_paths[len(kwargs["created_paths"])]
            kwargs["created_paths"].append(path)
            return SimpleNamespace(chemin_fichier=str(path))

        self.db.commit.side_effect = duplicate_error

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            return_value=_doc(34, 1),
        ), patch.object(
            document_service,
            "_apply_custom_fields",
            return_value=None,
        ), patch.object(
            attachment_service,
            "create",
            side_effect=create_attachment,
        ) as mock_attachment:
            with self.assertRaises(HTTPException) as ctx:
                document_service.create(
                    self.db,
                    payload,
                    user,
                    initial_files=[
                        _initial_file(),
                        UploadFile(
                            filename="second.pdf",
                            file=BytesIO(b"second"),
                        ),
                    ],
                )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(mock_attachment.call_count, 2)
        self.db.rollback.assert_called_once()
        for path in created_paths:
            self.assertFalse(path.exists())

    def test_other_integrity_error_is_not_transformed(self):
        user = _user(11, USER_ROLE_USER, ["document.create"], bureau_id=1)
        bureau = SimpleNamespace(id=1, circonscription_id=5)
        payload = DocumentCreate(
            reference_archive="REF-OTHER-INTEGRITY",
            nom_document="Autre erreur",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
        )
        other_error = IntegrityError(
            "insert",
            {},
            SimpleNamespace(
                sqlstate="23505",
                diag=SimpleNamespace(
                    constraint_name="documents_nom_document_key",
                ),
            ),
        )

        with patch(
            "app.services.document_service.document_field_repository.get_active",
            return_value=[],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=bureau,
        ), patch(
            "app.services.document_service.document_repository.create",
            side_effect=other_error,
        ):
            with self.assertRaises(IntegrityError) as ctx:
                document_service.create(
                    self.db,
                    payload,
                    user,
                    initial_file=_initial_file(),
                )

        self.assertIs(ctx.exception, other_error)
        self.db.rollback.assert_called_once()

    # TEST 18
    def test_user_bureau_1_update_circonscription_payload_ignoree(self):
        user = _user(11, USER_ROLE_USER, ["document.update"], bureau_id=1)
        target_doc = SimpleNamespace(
            id=18,
            bureau_id=1,
            nom_document="Avant",
            circonscription_id=5,
        )

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[target_doc, target_doc],
        ), patch(
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
            payload = DocumentUpdate(
                nom_document="Apres",
                circonscription_id=42,
            )
            result = document_service.update(
                self.db,
                18,
                payload,
                user,
            )

        self.assertEqual(result.id, 18)
        self.assertEqual(target_doc.nom_document, "Apres")
        self.assertEqual(target_doc.circonscription_id, 5)

    # TEST 19
    def test_admin_create_document_is_403_and_nothing_is_created(self):
        admin = _user(100, USER_ROLE_ADMIN, [])

        payload = DocumentCreate(
            reference_archive="REF-19",
            nom_document="Doc admin",
            date_creation=date(2026, 9, 1),
            type_document_id=1,
            circonscription_id=9,
        )

        with patch(
            "app.services.document_service.document_repository.create",
        ) as mock_create:
            with self.assertRaises(HTTPException) as ctx:
                document_service.create(self.db, payload, admin)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn(
            "reservee aux utilisateurs USER",
            ctx.exception.detail,
        )
        # Aucun document n'est cree en base apres le refus.
        mock_create.assert_not_called()

    # TEST 19b
    def test_admin_create_document_via_http_is_403(self):
        from fastapi.testclient import TestClient
        from app.database.session import get_db
        from app.main import app
        from app.security.dependencies import get_current_user

        admin = _user(100, USER_ROLE_ADMIN, [])
        admin.nom = "Admin"
        admin.prenom = "Root"
        admin.username = "admin"
        admin.actif = True
        admin.admin_circonscription_id = 1

        client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: admin

        try:
            response = client.post(
                "/documents/",
                json={
                    "reference_archive": "REF-HTTP-19",
                    "nom_document": "Doc admin http",
                    "date_creation": "2026-09-01",
                    "type_document_id": 1,
                },
            )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 403)

    # TEST 20
    def test_user_update_avec_demande_approuvee_temporaire_est_autorise(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)
        target_doc = _doc(20, 1, nom_document="Avant")

        approved_request = SimpleNamespace(
            id=50,
            user_id=11,
            bureau_id=1,
            permission="document.update",
            document_id=20,
            status="APPROVED",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[target_doc, target_doc],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(circonscription_id=1),
        ), patch(
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
        ), patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_request,
        ):
            payload = DocumentUpdate(nom_document="Apres")
            result = document_service.update(self.db, 20, payload, user)

        self.assertEqual(result.nom_document, "Apres")

    def test_admin_update_other_circonscription_is_403(self):
        admin = _user(
            100,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=2,
        )
        target_doc = _doc(25, 1, nom_document="Avant")

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            return_value=target_doc,
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(circonscription_id=1),
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.update(
                    self.db,
                    25,
                    DocumentUpdate(nom_document="Interdit"),
                    admin,
                )

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 21
    def test_user_update_sans_permission_et_demande_pending_est_refuse(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.update(
                    self.db,
                    21,
                    DocumentUpdate(nom_document="Interdit"),
                    user,
                )

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 22
    def test_user_update_demande_expiree_est_refuse(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        expired_request = SimpleNamespace(
            id=51,
            user_id=11,
            bureau_id=1,
            permission="document.update",
            document_id=22,
            status="APPROVED",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=expired_request,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=expired_request,
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.update(
                    self.db,
                    22,
                    DocumentUpdate(nom_document="Interdit"),
                    user,
                )

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 23
    def test_user_update_demande_autre_document_est_refuse(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        other_doc_request = SimpleNamespace(
            id=52,
            user_id=11,
            bureau_id=1,
            permission="document.update",
            document_id=999,
            status="APPROVED",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=other_doc_request,
        ):
            with self.assertRaises(HTTPException) as ctx:
                document_service.update(
                    self.db,
                    23,
                    DocumentUpdate(nom_document="Interdit"),
                    user,
                )

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 24
    def test_admin_update_sans_demande_fonctionne_toujours(self):
        admin = _user(
            100,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=1,
        )
        target_doc = _doc(24, 1, nom_document="Avant")

        with patch(
            "app.services.document_service.document_repository.get_by_id",
            side_effect=[target_doc, target_doc],
        ), patch(
            "app.services.document_service.bureau_repository.get_by_id",
            return_value=SimpleNamespace(circonscription_id=1),
        ), patch(
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
            result = document_service.update(self.db, 24, payload, admin)

        self.assertEqual(result.nom_document, "Apres")


if __name__ == "__main__":
    unittest.main()
