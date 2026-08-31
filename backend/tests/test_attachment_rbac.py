from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.services.attachment_service import attachment_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _document(document_id: int, bureau_id: int):
    return SimpleNamespace(
        id=document_id,
        bureau_id=bureau_id,
    )


def _attachment(attachment_id: int, document_id: int, path: str = "missing.bin"):
    return SimpleNamespace(
        id=attachment_id,
        document_id=document_id,
        chemin_fichier=path,
        type_mime="application/pdf",
        nom_original="piece.pdf",
    )


def _approved_request(user_id: int, bureau_id: int, permission: str, document_id=None, expired=False):
    delta = -5 if expired else 10
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission=permission,
        status="APPROVED",
        document_id=document_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=delta),
    )


class TestAttachmentRbac(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
            refresh=lambda _: None,
            add=lambda _: None,
        )

    # 1. ADMIN avec attachment.read -> autorise.
    def test_admin_attachment_read_list_by_document_allowed(self):
        admin = _user(1, USER_ROLE_ADMIN, permissions=[])
        doc = _document(10, bureau_id=3)
        expected = [_attachment(100, 10)]

        with patch("app.services.attachment_service.document_repository.get_by_id", return_value=doc), patch(
            "app.services.attachment_service.attachment_repository.get_by_document_id",
            return_value=expected,
        ):
            result = attachment_service.get_by_document_id(self.db, 10, admin)

        self.assertEqual(len(result), 1)

    # 2. USER avec attachment.read et document de son bureau -> autorise.
    def test_user_attachment_read_own_bureau_list_by_document_allowed(self):
        user = _user(11, USER_ROLE_USER, permissions=["attachment.read"], bureau_id=1)
        doc = _document(11, bureau_id=1)

        with patch("app.services.attachment_service.document_repository.get_by_id", return_value=doc), patch(
            "app.services.attachment_service.attachment_repository.get_by_document_id",
            return_value=[_attachment(101, 11)],
        ):
            result = attachment_service.get_by_document_id(self.db, 11, user)

        self.assertEqual(result[0].document_id, 11)

    # 3. USER avec attachment.read et document d'un autre bureau -> 403.
    def test_user_attachment_read_other_bureau_list_by_document_forbidden(self):
        user = _user(12, USER_ROLE_USER, permissions=["attachment.read"], bureau_id=1)

        with patch(
            "app.services.attachment_service.document_repository.get_by_id",
            side_effect=[None, _document(12, bureau_id=2)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_document_id(self.db, 12, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 4. USER sans attachment.read -> 403.
    def test_user_without_attachment_read_is_forbidden(self):
        user = _user(13, USER_ROLE_USER, permissions=[], bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_document_id(self.db, 13, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 5. USER avec permission temporaire valide attachment.read sur document -> autorise.
    def test_user_with_valid_temporary_attachment_read_is_allowed(self):
        user = _user(14, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved = _approved_request(
            user_id=14,
            bureau_id=1,
            permission="attachment.read",
            document_id=14,
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved,
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(14, bureau_id=1),
        ), patch(
            "app.services.attachment_service.attachment_repository.get_by_document_id",
            return_value=[_attachment(102, 14)],
        ):
            result = attachment_service.get_by_document_id(self.db, 14, user)

        self.assertEqual(len(result), 1)

    # 6. USER avec permission temporaire attachment.read expiree -> 403.
    def test_user_with_expired_temporary_attachment_read_is_forbidden(self):
        user = _user(15, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved_expired = _approved_request(
            user_id=15,
            bureau_id=1,
            permission="attachment.read",
            document_id=15,
            expired=True,
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_expired,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=approved_expired,
        ) as mock_mark_expired:
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_document_id(self.db, 15, user)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_mark_expired.assert_called_once()

    # 7. USER avec permission temporaire sur autre bureau -> 403.
    def test_user_temporary_attachment_read_other_bureau_is_forbidden(self):
        user = _user(16, USER_ROLE_USER, permissions=[], bureau_id=1)
        approved_other_bureau = _approved_request(
            user_id=16,
            bureau_id=2,
            permission="attachment.read",
            document_id=16,
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_other_bureau,
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_document_id(self.db, 16, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 8. ADMIN avec attachment.download -> autorise.
    def test_admin_attachment_download_allowed(self):
        admin = _user(2, USER_ROLE_ADMIN, permissions=[])

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(200, 20),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(20, bureau_id=4),
        ):
            result = attachment_service.get_by_id(self.db, 200, admin)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 200)

    # 9. USER avec attachment.download sur son bureau -> autorise.
    def test_user_attachment_download_own_bureau_allowed(self):
        user = _user(17, USER_ROLE_USER, permissions=["attachment.download"], bureau_id=2)

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(201, 21),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(21, bureau_id=2),
        ):
            result = attachment_service.get_by_id(self.db, 201, user)

        self.assertEqual(result.document_id, 21)

    # 10. USER avec attachment.download sur autre bureau -> 403.
    def test_user_attachment_download_other_bureau_forbidden(self):
        user = _user(18, USER_ROLE_USER, permissions=["attachment.download"], bureau_id=1)

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(202, 22),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(22, bureau_id=3),
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_id(self.db, 202, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 11. USER avec attachment.create sur son document -> autorise.
    def test_user_attachment_create_own_document_allowed(self):
        user = _user(19, USER_ROLE_USER, permissions=["attachment.create"], bureau_id=2)

        upload = UploadFile(
            filename="doc.txt",
            file=BytesIO(b"payload"),
        )

        with TemporaryDirectory() as temp_dir:
            def _create_side_effect(_, attachment):
                attachment.id = 301
                return attachment

            with patch("app.services.attachment_service.UPLOAD_DIR", Path(temp_dir)), patch(
                "app.services.attachment_service.document_repository.get_by_id",
                return_value=_document(23, bureau_id=2),
            ), patch(
                "app.services.attachment_service.attachment_repository.create",
                side_effect=_create_side_effect,
            ):
                created = attachment_service.create(self.db, 23, upload, user)

        self.assertEqual(created.document_id, 23)
        self.assertEqual(created.id, 301)

    # 12. USER avec attachment.create sur document d'un autre bureau -> 403.
    def test_user_attachment_create_other_bureau_document_forbidden(self):
        user = _user(20, USER_ROLE_USER, permissions=["attachment.create"], bureau_id=1)
        upload = UploadFile(
            filename="forbidden.txt",
            file=BytesIO(b"payload"),
        )

        with patch(
            "app.services.attachment_service.document_repository.get_by_id",
            side_effect=[None, _document(24, bureau_id=9)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.create(self.db, 24, upload, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 13. ADMIN avec attachment.delete -> autorise.
    def test_admin_attachment_delete_allowed(self):
        admin = _user(3, USER_ROLE_ADMIN, permissions=[])

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(401, 31),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(31, bureau_id=7),
        ), patch(
            "app.services.attachment_service.attachment_repository.delete",
            return_value=True,
        ) as mock_delete:
            result = attachment_service.delete(self.db, 401, admin)

        self.assertTrue(result)
        mock_delete.assert_called_once()

    # 14. USER avec attachment.delete sur son bureau -> autorise.
    def test_user_attachment_delete_own_bureau_allowed(self):
        user = _user(21, USER_ROLE_USER, permissions=["attachment.delete"], bureau_id=5)

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(402, 32),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(32, bureau_id=5),
        ), patch(
            "app.services.attachment_service.attachment_repository.delete",
            return_value=True,
        ):
            result = attachment_service.delete(self.db, 402, user)

        self.assertTrue(result)

    # 15. USER avec attachment.delete sur autre bureau -> 403.
    def test_user_attachment_delete_other_bureau_forbidden(self):
        user = _user(22, USER_ROLE_USER, permissions=["attachment.delete"], bureau_id=1)

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=_attachment(403, 33),
        ), patch(
            "app.services.attachment_service.document_repository.get_by_id",
            return_value=_document(33, bureau_id=8),
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.delete(self.db, 403, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 16. Piece jointe inexistante -> 404 (via router), service retourne None/False.
    def test_attachment_not_found_service_returns_none_or_false(self):
        user = _user(23, USER_ROLE_USER, permissions=["attachment.download", "attachment.delete"], bureau_id=1)

        with patch(
            "app.services.attachment_service.attachment_repository.get_by_id",
            return_value=None,
        ):
            self.assertIsNone(attachment_service.get_by_id(self.db, 999, user))
            self.assertFalse(attachment_service.delete(self.db, 999, user))

    # 17. Document inexistant lors d'un upload -> 404.
    def test_upload_document_not_found_is_404(self):
        user = _user(24, USER_ROLE_USER, permissions=["attachment.create"], bureau_id=1)
        upload = UploadFile(
            filename="missing.txt",
            file=BytesIO(b"payload"),
        )

        with patch(
            "app.services.attachment_service.document_repository.get_by_id",
            side_effect=[None, None],
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.create(self.db, 777, upload, user)

        self.assertEqual(ctx.exception.status_code, 404)

    # 18. GET global /documents/attachments/all : ADMIN toutes, USER scope bureau.
    def test_global_list_admin_and_user_scope(self):
        admin = _user(4, USER_ROLE_ADMIN, permissions=[])
        user = _user(25, USER_ROLE_USER, permissions=["attachment.read"], bureau_id=2)

        with patch(
            "app.services.attachment_service.attachment_repository.get_all",
            return_value=[_attachment(501, 40), _attachment(502, 41)],
        ) as mock_get_all, patch(
            "app.services.attachment_service.attachment_repository.get_all_by_bureau",
            return_value=[_attachment(503, 42)],
        ) as mock_get_all_by_bureau:
            admin_result = attachment_service.get_all(self.db, admin)
            user_result = attachment_service.get_all(self.db, user)

        self.assertEqual(len(admin_result), 2)
        self.assertEqual(len(user_result), 1)
        mock_get_all.assert_called_once_with(self.db)
        mock_get_all_by_bureau.assert_called_once_with(self.db, bureau_id=2)

    # 19. Une permission inconnue n'est jamais acceptee.
    def test_unknown_permission_is_rejected(self):
        user = _user(26, USER_ROLE_USER, permissions=["attachment.read"], bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            attachment_service._ensure_permission(
                self.db,
                user,
                "attachment.unknown",
                bureau_id=1,
            )

        self.assertEqual(ctx.exception.status_code, 403)

    # 20. Aucun USER ne peut contourner le scope bureau avec une permission permanente.
    def test_user_cannot_bypass_bureau_scope_with_permanent_permission(self):
        user = _user(27, USER_ROLE_USER, permissions=["attachment.read"], bureau_id=1)

        with patch(
            "app.services.attachment_service.document_repository.get_by_id",
            side_effect=[None, _document(88, bureau_id=9)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_by_document_id(self.db, 88, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 21. Une permission temporaire expiree ne donne plus acces (global read).
    def test_expired_temporary_permission_no_longer_grants_global_read(self):
        user = _user(28, USER_ROLE_USER, permissions=[], bureau_id=3)
        approved_expired = _approved_request(
            user_id=28,
            bureau_id=3,
            permission="attachment.read",
            document_id=None,
            expired=True,
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=approved_expired,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=approved_expired,
        ) as mock_mark_expired:
            with self.assertRaises(HTTPException) as ctx:
                attachment_service.get_all(self.db, user)

        self.assertEqual(ctx.exception.status_code, 403)
        mock_mark_expired.assert_called_once()


if __name__ == "__main__":
    unittest.main()
