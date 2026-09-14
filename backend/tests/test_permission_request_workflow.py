from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.audit_log import AuditLog
from app.models.bureau import Bureau
from app.models.circonscription import Circonscription
from app.models.document import Document
from app.models.notification import Notification
from app.models.permission_request import PermissionRequest
from app.models.permission_request import PERMISSION_REQUEST_STATUS_APPROVED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_PENDING
from app.models.permission_request import PERMISSION_REQUEST_STATUS_REJECTED
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER, User
from app.security.authorization import has_temporary_permission
from app.security.authorization import has_effective_permission
from app.services.permission_request_service import permission_request_service


def _user(user_id: int, role: str, permissions=None, bureau_id=None, admin_circonscription_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
        admin_circonscription_id=admin_circonscription_id,
    )


def _request(
    request_id: int,
    user_id: int,
    bureau_id: int,
    permission: str,
    status: str,
    document_id=None,
    reviewed_by=None,
    expires_at=None,
):
    return SimpleNamespace(
        id=request_id,
        user_id=user_id,
        bureau_id=bureau_id,
        permission=permission,
        document_id=document_id,
        reason=None,
        status=status,
        requested_at=datetime.now(timezone.utc),
        reviewed_at=None,
        reviewed_by=reviewed_by,
        expires_at=expires_at,
    )


class TestPermissionRequestWorkflow(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
            refresh=lambda _: None,
            add=lambda _: None,
            rollback=lambda: None,
            flush=lambda: None,
        )

    # 1. USER peut creer une demande.
    def test_user_can_create_request(self):
        user = _user(10, USER_ROLE_USER, bureau_id=1)
        payload = SimpleNamespace(permission="document.update", document_id=8, reason="Besoin")

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=8, bureau_id=1),
        ), patch(
            "app.services.permission_request_service.permission_request_repository.find_pending_duplicate",
            return_value=None,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create",
        ) as mock_create:
            mock_create.side_effect = lambda _db, request, **kwargs: request
            result = permission_request_service.create(self.db, user, payload)

        self.assertEqual(result.user_id, 10)
        self.assertEqual(result.bureau_id, 1)
        self.assertEqual(result.status, PERMISSION_REQUEST_STATUS_PENDING)

    def test_document_update_request_requires_document_id(self):
        user = _user(10, USER_ROLE_USER, bureau_id=1)
        payload = SimpleNamespace(
            permission="document.update",
            document_id=None,
            reason="Besoin",
        )

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 400)

    # 2. user_id est impose par le backend.
    def test_user_id_is_enforced_by_backend(self):
        user = _user(33, USER_ROLE_USER, bureau_id=1)
        payload = SimpleNamespace(permission="document.read", document_id=None, reason=None)

        with patch(
            "app.services.permission_request_service.permission_request_repository.find_pending_duplicate",
            return_value=None,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create",
        ) as mock_create:
            mock_create.side_effect = lambda _db, request, **kwargs: request
            permission_request_service.create(self.db, user, payload)

        created_request = mock_create.call_args.kwargs["request"]
        self.assertEqual(created_request.user_id, 33)

    # 3. bureau_id est impose par le backend.
    def test_bureau_id_is_enforced_by_backend(self):
        user = _user(33, USER_ROLE_USER, bureau_id=2)
        payload = SimpleNamespace(permission="document.read", document_id=None, reason=None)

        with patch(
            "app.services.permission_request_service.permission_request_repository.find_pending_duplicate",
            return_value=None,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create",
        ) as mock_create:
            mock_create.side_effect = lambda _db, request, **kwargs: request
            permission_request_service.create(self.db, user, payload)

        created_request = mock_create.call_args.kwargs["request"]
        self.assertEqual(created_request.bureau_id, 2)

    # 4. permission inconnue rejetee.
    def test_unknown_permission_is_rejected(self):
        user = _user(33, USER_ROLE_USER, bureau_id=2)
        payload = SimpleNamespace(permission="document.unknown", document_id=None, reason=None)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 400)

    # 5. USER ne peut demander pour un document d'un autre bureau.
    def test_user_cannot_request_other_bureau_document(self):
        user = _user(33, USER_ROLE_USER, bureau_id=2)
        payload = SimpleNamespace(permission="document.read", document_id=9, reason=None)

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            side_effect=[None, SimpleNamespace(id=9, bureau_id=1)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 403)

    # 6. USER peut consulter ses propres demandes.
    def test_user_can_read_own_requests(self):
        user = _user(41, USER_ROLE_USER, bureau_id=1)
        expected = [_request(1, 41, 1, "document.read", PERMISSION_REQUEST_STATUS_PENDING)]

        with patch(
            "app.services.permission_request_service.permission_request_repository.get_by_user_id",
            return_value=expected,
        ):
            result = permission_request_service.get_me(self.db, user)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].user_id, 41)

    # 7. USER ne voit pas les demandes des autres utilisateurs.
    def test_user_scope_for_me_requests(self):
        user = _user(50, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.services.permission_request_service.permission_request_repository.get_by_user_id",
            return_value=[],
        ) as mock_get:
            permission_request_service.get_me(self.db, user)

        mock_get.assert_called_once_with(self.db, 50)

    # 8. USER ne peut pas consulter les demandes globales ADMIN.
    def test_user_cannot_read_global_requests(self):
        user = _user(51, USER_ROLE_USER, bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.get_all(self.db, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 9. USER ne peut pas approuver.
    def test_user_cannot_approve(self):
        user = _user(52, USER_ROLE_USER, bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.approve(self.db, 1, 30, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 10. USER ne peut pas refuser.
    def test_user_cannot_reject(self):
        user = _user(52, USER_ROLE_USER, bureau_id=1)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.reject(self.db, 1, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 11. ADMIN peut consulter toutes les demandes.
    def test_admin_can_read_all_requests(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        expected = [
            _request(1, 10, 1, "document.read", PERMISSION_REQUEST_STATUS_PENDING),
            _request(2, 11, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING),
        ]

        with patch.object(
            permission_request_service,
            "_scoped_query",
        ) as mock_scoped:
            mock_scoped.return_value.order_by.return_value.all.return_value = expected
            result = permission_request_service.get_all(self.db, admin)

        self.assertEqual(len(result), 2)

    # 12. ADMIN peut approuver.
    def test_admin_can_approve(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(10, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.approve",
            side_effect=lambda _db, request, reviewed_by, reviewed_at, expires_at, **kwargs: SimpleNamespace(
                id=request.id,
                user_id=request.user_id,
                bureau_id=request.bureau_id,
                permission=request.permission,
                document_id=request.document_id,
                status=PERMISSION_REQUEST_STATUS_APPROVED,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                expires_at=expires_at,
            ),
        ):
            result = permission_request_service.approve(self.db, 10, 30, admin)

        self.assertEqual(result.status, PERMISSION_REQUEST_STATUS_APPROVED)
        self.assertEqual(result.reviewed_by, 1)

    def test_document_update_approval_creates_attachment_companion(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(101, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING, document_id=8)
        companion_calls = []

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.approve",
            side_effect=lambda _db, request, reviewed_by, reviewed_at, expires_at, **kwargs: SimpleNamespace(
                id=request.id,
                user_id=request.user_id,
                bureau_id=request.bureau_id,
                permission=request.permission,
                document_id=request.document_id,
                reason=request.reason,
                status=PERMISSION_REQUEST_STATUS_APPROVED,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                expires_at=expires_at,
            ),
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create_approved_companion",
            side_effect=lambda *args, **kwargs: companion_calls.append(kwargs),
        ):
            result = permission_request_service.approve(self.db, 101, 1, admin)

        self.assertEqual(len(companion_calls), 1)
        companion = companion_calls[0]
        self.assertEqual(companion["permission"], "attachment.create")
        self.assertEqual(companion["source_request"].document_id, result.document_id)
        self.assertEqual(companion["expires_at"], result.expires_at)

    def test_companion_creation_failure_rolls_back_approval(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(102, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING, document_id=8)
        self.db.rollback = MagicMock()

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.approve",
            return_value=SimpleNamespace(
                id=102,
                user_id=33,
                bureau_id=2,
                permission="document.update",
                document_id=8,
                reason=None,
                status=PERMISSION_REQUEST_STATUS_APPROVED,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            ),
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create_approved_companion",
            side_effect=RuntimeError("companion failure"),
        ):
            with self.assertRaises(RuntimeError):
                permission_request_service.approve(self.db, 102, 1, admin)

        self.assertTrue(self.db.rollback.called)

    def test_update_and_attachment_permissions_share_effective_expiration_and_scope(self):
        user = _user(103, USER_ROLE_USER, bureau_id=2)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=1)
        requests = {
            "document.update": _request(
                1031, 103, 2, "document.update", PERMISSION_REQUEST_STATUS_APPROVED,
                document_id=8, expires_at=expires_at,
            ),
            "attachment.create": _request(
                1032, 103, 2, "attachment.create", PERMISSION_REQUEST_STATUS_APPROVED,
                document_id=8, expires_at=expires_at,
            ),
        }

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            side_effect=lambda _db, permission, **kwargs: requests[permission],
        ):
            self.assertTrue(has_effective_permission(self.db, user, "document.update", document_id=8, bureau_id=2))
            self.assertTrue(has_effective_permission(self.db, user, "attachment.create", document_id=8, bureau_id=2))
            self.assertFalse(has_effective_permission(self.db, user, "attachment.create", document_id=9, bureau_id=2))

        expired = expires_at - timedelta(minutes=2)
        requests["document.update"].expires_at = expired
        requests["attachment.create"].expires_at = expired

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            side_effect=lambda _db, permission, **kwargs: requests[permission],
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
        ):
            self.assertFalse(has_effective_permission(self.db, user, "document.update", document_id=8, bureau_id=2))
            self.assertFalse(has_effective_permission(self.db, user, "attachment.create", document_id=8, bureau_id=2))

    # 13. ADMIN peut refuser.
    def test_admin_can_reject(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(11, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.reject",
            side_effect=lambda _db, request, reviewed_by, reviewed_at, **kwargs: SimpleNamespace(
                id=request.id,
                user_id=request.user_id,
                bureau_id=request.bureau_id,
                permission=request.permission,
                document_id=request.document_id,
                status=PERMISSION_REQUEST_STATUS_REJECTED,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                expires_at=None,
            ),
        ):
            result = permission_request_service.reject(self.db, 11, admin)

        self.assertEqual(result.status, PERMISSION_REQUEST_STATUS_REJECTED)
        self.assertEqual(result.reviewed_by, 1)

    def test_approve_already_processed_request_returns_conflict(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(18, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING, document_id=8)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.approve",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.approve(self.db, 18, 30, admin)

        self.assertEqual(ctx.exception.status_code, 409)

    def test_reject_already_processed_request_returns_conflict(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(19, 33, 2, "document.update", PERMISSION_REQUEST_STATUS_PENDING, document_id=8)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.reject",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.reject(self.db, 19, admin)

        self.assertEqual(ctx.exception.status_code, 409)

    def test_pending_unique_conflict_is_returned_as_409(self):
        user = _user(76, USER_ROLE_USER, bureau_id=3)
        payload = SimpleNamespace(
            permission="document.update",
            document_id=8,
            reason=None,
        )
        original = SimpleNamespace(
            sqlstate="23505",
            diag=SimpleNamespace(
                constraint_name="uq_permission_requests_pending_scope",
            ),
        )

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=8, bureau_id=3),
        ), patch(
            "app.services.permission_request_service.permission_request_repository.find_pending_duplicate",
            return_value=None,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.create",
            side_effect=IntegrityError("insert", {}, original),
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 409)

    # 14. Une demande approuvee possede expires_at.
    def test_approved_request_has_expires_at(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)
        pending = _request(12, 33, 2, "document.read", PERMISSION_REQUEST_STATUS_PENDING)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.approve",
            side_effect=lambda _db, request, reviewed_by, reviewed_at, expires_at, **kwargs: SimpleNamespace(
                id=request.id,
                user_id=request.user_id,
                bureau_id=request.bureau_id,
                permission=request.permission,
                document_id=request.document_id,
                status=PERMISSION_REQUEST_STATUS_APPROVED,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
                expires_at=expires_at,
            ),
        ):
            result = permission_request_service.approve(self.db, 12, 45, admin)

        self.assertIsNotNone(result.expires_at)

    # 15. Une demande expiree n'accorde plus la permission.
    def test_expired_request_does_not_grant_permission(self):
        user = _user(70, USER_ROLE_USER, permissions=[], bureau_id=2)
        expired = _request(
            13,
            70,
            2,
            "document.read",
            PERMISSION_REQUEST_STATUS_APPROVED,
            document_id=5,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=expired,
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
            return_value=expired,
        ) as mock_mark_expired:
            granted = has_temporary_permission(
                self.db,
                user,
                "document.read",
                document_id=5,
                bureau_id=2,
            )

        self.assertFalse(granted)
        mock_mark_expired.assert_called_once()

    # 16. Une demande refusee n'accorde pas la permission.
    def test_rejected_request_does_not_grant_permission(self):
        user = _user(71, USER_ROLE_USER, permissions=[], bureau_id=2)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
            granted = has_temporary_permission(
                self.db,
                user,
                "document.update",
                document_id=5,
                bureau_id=2,
            )

        self.assertFalse(granted)

    # 17. USER peut annuler une demande PENDING qui lui appartient.
    def test_user_can_cancel_own_pending_request(self):
        user = _user(72, USER_ROLE_USER, bureau_id=2)
        pending = _request(14, 72, 2, "document.read", PERMISSION_REQUEST_STATUS_PENDING)

        with patch(
            "app.services.permission_request_service.permission_request_repository.get_by_id",
            return_value=pending,
        ), patch(
            "app.services.permission_request_service.permission_request_repository.cancel",
            side_effect=lambda _db, request: SimpleNamespace(id=request.id, status="CANCELLED"),
        ):
            result = permission_request_service.cancel(self.db, 14, user)

        self.assertEqual(result.status, "CANCELLED")

    # 18. USER ne peut pas annuler la demande d'un autre utilisateur.
    def test_user_cannot_cancel_other_user_request(self):
        user = _user(73, USER_ROLE_USER, bureau_id=2)
        other_pending = _request(15, 99, 2, "document.read", PERMISSION_REQUEST_STATUS_PENDING)

        with patch(
            "app.services.permission_request_service.permission_request_repository.get_by_id",
            return_value=other_pending,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.cancel(self.db, 15, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 19. Une demande deja traitee ne peut pas etre modifiee.
    def test_processed_request_cannot_be_cancelled(self):
        user = _user(74, USER_ROLE_USER, bureau_id=2)
        approved = _request(16, 74, 2, "document.read", PERMISSION_REQUEST_STATUS_APPROVED)

        with patch(
            "app.services.permission_request_service.permission_request_repository.get_by_id",
            return_value=approved,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.cancel(self.db, 16, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # 20. Une demande PENDING identique ne peut pas etre creee deux fois.
    def test_duplicate_pending_request_is_rejected(self):
        user = _user(75, USER_ROLE_USER, bureau_id=3)
        payload = SimpleNamespace(permission="document.read", document_id=8, reason=None)

        duplicate = _request(17, 75, 3, "document.read", PERMISSION_REQUEST_STATUS_PENDING, document_id=8)

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=8, bureau_id=3),
        ), patch(
            "app.services.permission_request_service.permission_request_repository.find_pending_duplicate",
            return_value=duplicate,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 409)

    # 21. ADMIN sans circonscription ne peut pas consulter les demandes.
    def test_admin_without_circonscription_cannot_list_requests(self):
        admin = _user(1, USER_ROLE_ADMIN)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.get_pending(self.db, admin)

        self.assertEqual(ctx.exception.status_code, 403)

    # 22. ADMIN Gombe: pending scope a la circonscription 1.
    def test_admin_gombe_pending_scoped_to_circonscription(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []

        self.db.query = MagicMock(return_value=mock_query)

        result = permission_request_service.get_pending(self.db, admin)

        self.assertEqual(result, [])
        self.db.query.assert_called_once()
        mock_query.join.assert_called_once()
        # La jointure et le filtre circonscription ont ete appliques
        filter_calls = mock_query.filter.call_args_list
        self.assertTrue(len(filter_calls) >= 1)

    # 23. ADMIN Gombe ne peut pas approuver une demande hors scope.
    def test_admin_gombe_cannot_approve_other_circonscription_request(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.approve(self.db, 99, 30, admin)

        self.assertEqual(ctx.exception.status_code, 404)

    # 24. ADMIN Gombe ne peut pas refuser une demande hors scope.
    def test_admin_gombe_cannot_reject_other_circonscription_request(self):
        admin = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=1)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                permission_request_service.reject(self.db, 99, admin)

        self.assertEqual(ctx.exception.status_code, 404)


class TestPermissionRequestAuditLogTransaction(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        PermissionRequest.__table__.create(bind=self.engine)
        AuditLog.__table__.create(bind=self.engine)
        Notification.__table__.create(bind=self.engine)
        Bureau.__table__.create(bind=self.engine, checkfirst=True)
        Circonscription.__table__.create(bind=self.engine, checkfirst=True)
        Document.__table__.create(bind=self.engine, checkfirst=True)

        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        real_query = self.db.query
        def safe_query(model, *args, **kwargs):
            if model == User:
                m = MagicMock()
                m.filter.return_value = m
                m.all.return_value = []
                return m
            return real_query(model, *args, **kwargs)

        self.db.query = safe_query

    def tearDown(self):
        self.db.close()

    # TEST 1 — SUCCÈS
    def test_permission_request_creation_creates_atomic_audit_log(self):
        user = _user(10, USER_ROLE_USER, bureau_id=1)
        user.bureau = SimpleNamespace(id=1, circonscription_id=100)
        payload = SimpleNamespace(permission="document.update", document_id=8, reason="Raison de test")

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=8, bureau_id=1),
        ):
            req = permission_request_service.create(self.db, user, payload)

        # Vérification PermissionRequest
        saved_req = self.db.query(PermissionRequest).filter(PermissionRequest.id == req.id).first()
        self.assertIsNotNone(saved_req)
        self.assertEqual(saved_req.status, PERMISSION_REQUEST_STATUS_PENDING)

        # Vérification AuditLog
        logs = self.db.query(AuditLog).all()
        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertEqual(log.action, "permission_request.created")
        self.assertEqual(log.entity_type, "PermissionRequest")
        self.assertEqual(log.entity_id, req.id)
        self.assertEqual(log.permission_request_id, req.id)
        self.assertEqual(log.actor_user_id, 10)
        self.assertEqual(log.document_id, 8)
        self.assertEqual(log.bureau_id, 1)
        self.assertEqual(log.circonscription_id, 100)
        self.assertIsNone(log.old_state)
        self.assertEqual(log.new_state["permission"], "document.update")
        self.assertEqual(log.new_state["document_id"], 8)
        self.assertEqual(log.new_state["reason"], "Raison de test")
        self.assertEqual(log.new_state["status"], "PENDING")

    # TEST 2 — ÉCHEC AUDITLOG -> ROLLBACK ATOMIQUE
    def test_audit_log_failure_rolls_back_permission_request(self):
        user = _user(11, USER_ROLE_USER, bureau_id=1)
        user.bureau = SimpleNamespace(id=1, circonscription_id=100)
        payload = SimpleNamespace(permission="document.read", document_id=None, reason="Lecture")

        with patch(
            "app.services.permission_request_service.audit_log_service.log_event",
            side_effect=RuntimeError("Erreur audit simulee"),
        ):
            with self.assertRaises(RuntimeError):
                permission_request_service.create(self.db, user, payload)

        self.assertEqual(self.db.query(PermissionRequest).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    # TEST 3 — ÉCHEC PERMISSIONREQUEST / DOUBLON
    def test_duplicate_pending_rejected_with_no_additional_audit_log(self):
        user = _user(12, USER_ROLE_USER, bureau_id=1)
        user.bureau = SimpleNamespace(id=1, circonscription_id=100)
        payload = SimpleNamespace(permission="document.read", document_id=None, reason="Lecture")

        req1 = permission_request_service.create(self.db, user, payload)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

        with self.assertRaises(HTTPException) as ctx:
            permission_request_service.create(self.db, user, payload)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "Une demande identique est deja en attente.")
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    # TEST 4 — INTÉGRITÉ DES RÉFÉRENCES
    def test_audit_log_references_integrity_enforced_by_backend(self):
        user = _user(15, USER_ROLE_USER, bureau_id=2)
        user.bureau = SimpleNamespace(id=2, circonscription_id=200)
        payload = SimpleNamespace(permission="document.update", document_id=12, reason="Audit ref")

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=12, bureau_id=2),
        ):
            req = permission_request_service.create(self.db, user, payload)

        log = self.db.query(AuditLog).filter(AuditLog.permission_request_id == req.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor_user_id, 15)
        self.assertEqual(log.bureau_id, 2)
        self.assertEqual(log.circonscription_id, 200)
        self.assertEqual(log.document_id, 12)
        self.assertEqual(log.permission_request_id, req.id)

    # TEST 5 — DONNÉES SENSIBLES
    def test_sensitive_data_absent_from_audit_log(self):
        user = _user(16, USER_ROLE_USER, bureau_id=1)
        user.bureau = SimpleNamespace(id=1, circonscription_id=100)
        payload = SimpleNamespace(permission="document.read", document_id=None, reason="Demande standard")

        req = permission_request_service.create(self.db, user, payload)
        log = self.db.query(AuditLog).filter(AuditLog.permission_request_id == req.id).first()

        self.assertNotIn("password", log.new_state)
        self.assertNotIn("token", log.new_state)
        self.assertNotIn("jwt", log.new_state)
        self.assertNotIn("secret", log.new_state)

    # TEST 6 — NOTIFICATION ADMIN À LA CRÉATION
    def test_permission_request_creation_notifies_admins_of_circonscription(self):
        user = _user(20, USER_ROLE_USER, bureau_id=1)
        user.bureau = SimpleNamespace(id=1, circonscription_id=100)
        user.nom = "Kabila"
        user.prenom = "Joseph"

        admin_100 = _user(101, USER_ROLE_ADMIN, admin_circonscription_id=100)
        mock_admin_query = MagicMock()
        mock_admin_query.filter.return_value.all.return_value = [admin_100]

        original_query = self.db.query

        def custom_query(model, *args, **kwargs):
            if model == User:
                return mock_admin_query
            return original_query(model, *args, **kwargs)

        payload = SimpleNamespace(permission="document.update", document_id=15, reason="Modif projet")

        with patch(
            "app.services.permission_request_service.document_repository.get_by_id",
            return_value=SimpleNamespace(id=15, bureau_id=1),
        ), patch.object(self.db, "query", side_effect=custom_query):
            req = permission_request_service.create(self.db, user, payload)

        # Vérifier la notification de l'ADMIN de la circonscription 100
        notifs_100 = self.db.query(Notification).filter(Notification.recipient_user_id == 101).all()
        self.assertEqual(len(notifs_100), 1)
        notif = notifs_100[0]
        self.assertEqual(notif.action, "permission_request.created")
        self.assertEqual(notif.permission_request_id, req.id)
        self.assertEqual(notif.document_id, 15)
        self.assertEqual(notif.bureau_id, 1)
        self.assertEqual(notif.circonscription_id, 100)
        self.assertIn("Joseph Kabila", notif.message)

    # TEST 7 — APPROBATION -> AUDITLOG + NOTIFICATION USER
    def test_permission_request_approve_notifies_user_and_logs_audit(self):
        # Préparation de la demande PENDING en base
        req = PermissionRequest(
            user_id=25,
            bureau_id=2,
            permission="document.update",
            document_id=30,
            status=PERMISSION_REQUEST_STATUS_PENDING,
        )
        self.db.add(req)
        self.db.commit()

        admin = _user(100, USER_ROLE_ADMIN, admin_circonscription_id=10)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=req,
        ):
            approved = permission_request_service.approve(self.db, req.id, duration_minutes=60, current_user=admin)

        self.assertEqual(approved.status, PERMISSION_REQUEST_STATUS_APPROVED)
        self.assertIsNotNone(approved.expires_at)

        # Vérification AuditLog
        log = self.db.query(AuditLog).filter(
            AuditLog.permission_request_id == req.id,
            AuditLog.action == "permission_request.approved",
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor_user_id, 100)

        # Vérification Notification vers USER 25
        notif = self.db.query(Notification).filter(
            Notification.recipient_user_id == 25,
            Notification.action == "permission_request.approved",
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.permission_request_id, req.id)
        self.assertEqual(notif.document_id, 30)
        self.assertIn("60 minute(s)", notif.message)

    # TEST 8 — REJET -> AUDITLOG + NOTIFICATION USER
    def test_permission_request_reject_notifies_user_and_logs_audit(self):
        req = PermissionRequest(
            user_id=26,
            bureau_id=2,
            permission="document.update",
            document_id=31,
            status=PERMISSION_REQUEST_STATUS_PENDING,
        )
        self.db.add(req)
        self.db.commit()

        admin = _user(100, USER_ROLE_ADMIN, admin_circonscription_id=10)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=req,
        ):
            rejected = permission_request_service.reject(self.db, req.id, current_user=admin)

        self.assertEqual(rejected.status, PERMISSION_REQUEST_STATUS_REJECTED)

        # Vérification AuditLog
        log = self.db.query(AuditLog).filter(
            AuditLog.permission_request_id == req.id,
            AuditLog.action == "permission_request.rejected",
        ).first()
        self.assertIsNotNone(log)

        # Vérification Notification vers USER 26
        notif = self.db.query(Notification).filter(
            Notification.recipient_user_id == 26,
            Notification.action == "permission_request.rejected",
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.permission_request_id, req.id)

    # TEST 9 — ÉCHEC NOTIFICATION SUR APPROBATION -> ROLLBACK COMPLET
    def test_approve_notification_failure_causes_rollback(self):
        req = PermissionRequest(
            user_id=27,
            bureau_id=2,
            permission="document.update",
            document_id=32,
            status=PERMISSION_REQUEST_STATUS_PENDING,
        )
        self.db.add(req)
        self.db.commit()

        admin = _user(100, USER_ROLE_ADMIN, admin_circonscription_id=10)

        with patch.object(
            permission_request_service,
            "_get_scoped_request",
            return_value=req,
        ), patch(
            "app.services.permission_request_service.notification_service.notify_user",
            side_effect=RuntimeError("Erreur notification simulee"),
        ):
            with self.assertRaises(RuntimeError):
                permission_request_service.approve(self.db, req.id, duration_minutes=15, current_user=admin)

        # La demande doit rester PENDING
        refreshed_req = self.db.query(PermissionRequest).filter(PermissionRequest.id == req.id).first()
        self.assertEqual(refreshed_req.status, PERMISSION_REQUEST_STATUS_PENDING)

        # Aucun AuditLog ou Notification enregistré
        self.assertEqual(self.db.query(AuditLog).filter(AuditLog.permission_request_id == req.id).count(), 0)
        self.assertEqual(self.db.query(Notification).filter(Notification.permission_request_id == req.id).count(), 0)


if __name__ == "__main__":
    unittest.main()
