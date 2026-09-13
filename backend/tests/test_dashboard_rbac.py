from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.dashboard_router import get_dashboard_stats
from app.models.document import Document
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER


def _user(user_id: int, role: str, permissions=None, bureau_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
    )


def _approved_request(user_id: int, bureau_id: int, expired=False):
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        bureau_id=bureau_id,
        permission="dashboard.read",
        status="APPROVED",
        document_id=None,
        expires_at=datetime.now(timezone.utc) + timedelta(
            minutes=-5 if expired else 10
        ),
    )


class _DashboardDb:

    def __init__(self):
        self.queries = []

    def query(self, *args):
        query = MagicMock()
        query.filter.return_value = query
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.group_by.return_value = query
        query.order_by.return_value = query
        query.limit.return_value = query
        query.scalar.return_value = 0
        query.all.return_value = []
        self.queries.append(query)
        return query


def _contains_bureau_filter(expression, bureau_id: int) -> bool:
    left = getattr(expression, "left", None)
    right = getattr(expression, "right", None)

    if (
        left is not None
        and left.compare(Document.bureau_id.expression)
        and getattr(right, "value", None) == bureau_id
    ):
        return True

    return any(
        _contains_bureau_filter(child, bureau_id)
        for child in expression.get_children()
    )


class TestDashboardRbac(unittest.TestCase):

    def test_admin_with_dashboard_read_keeps_global_dashboard(self):
        db = _DashboardDb()
        admin = _user(1, USER_ROLE_ADMIN)

        result = get_dashboard_stats(db, admin)

        self.assertEqual(result["summary"]["total_documents"], 0)
        self.assertFalse(
            any(
                _contains_bureau_filter(argument, 1)
                for query in db.queries
                for call in query.filter.call_args_list
                for argument in call.args
            )
        )

    def test_each_gombe_user_sees_only_own_bureau_statistics(self):
        for bureau_id in (1, 2, 3, 4):
            with self.subTest(bureau_id=bureau_id):
                db = _DashboardDb()
                user = _user(
                    bureau_id,
                    USER_ROLE_USER,
                    permissions=["dashboard.read"],
                    bureau_id=bureau_id,
                )

                get_dashboard_stats(db, user)

                self.assertTrue(
                    any(
                        _contains_bureau_filter(argument, bureau_id)
                        for query in db.queries
                        for call in query.filter.call_args_list
                        for argument in call.args
                    )
                )

    def test_user_without_dashboard_read_is_forbidden(self):
        db = _DashboardDb()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ), self.assertRaises(HTTPException) as context:
            get_dashboard_stats(db, user)

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(db.queries, [])

    def test_user_without_bureau_is_forbidden(self):
        db = _DashboardDb()
        user = _user(2, USER_ROLE_USER, permissions=["dashboard.read"])

        with self.assertRaises(HTTPException) as context:
            get_dashboard_stats(db, user)

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(db.queries, [])

    def test_valid_temporary_dashboard_permission_is_allowed_in_own_bureau(self):
        db = _DashboardDb()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 1),
        ):
            get_dashboard_stats(db, user)

        self.assertTrue(db.queries)

    def test_expired_temporary_dashboard_permission_is_forbidden(self):
        db = _DashboardDb()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 1, expired=True),
        ), patch(
            "app.security.authorization.permission_request_repository.mark_expired",
        ) as mark_expired, self.assertRaises(HTTPException) as context:
            get_dashboard_stats(db, user)

        self.assertEqual(context.exception.status_code, 403)
        mark_expired.assert_called_once()

    def test_temporary_permission_for_another_bureau_is_forbidden(self):
        db = _DashboardDb()
        user = _user(2, USER_ROLE_USER, bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=_approved_request(2, 2),
        ), self.assertRaises(HTTPException) as context:
            get_dashboard_stats(db, user)

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(db.queries, [])