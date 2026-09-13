from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.notification import Notification
from app.models.permission_request import PermissionRequest
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER, User
from app.repositories.notification_repository import notification_repository
from app.security.dependencies import get_current_user
from app.security.permissions import (
    PERMISSION_NOTIFICATION_MARK_READ,
    PERMISSION_NOTIFICATION_READ,
)


def _user(
    user_id: int,
    role: str = USER_ROLE_USER,
    permissions=None,
    bureau_id=None,
    admin_circonscription_id=None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
        admin_circonscription_id=admin_circonscription_id,
        actif=True,
        username=f"user_{user_id}",
    )


class TestNotificationRouterHttp(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Notification.__table__.create(bind=self.engine)
        PermissionRequest.__table__.create(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def _override_user(self, user):
        app.dependency_overrides[get_current_user] = lambda: user

    # 1. Authentication requise (401 avec token invalide, 403 sans en-tête)
    def test_unauthenticated_request_returns_401_or_403(self):
        app.dependency_overrides.pop(get_current_user, None)
        invalid_headers = {"Authorization": "Bearer invalid_token_123"}

        res_invalid_token = self.client.get("/notifications", headers=invalid_headers)
        self.assertEqual(res_invalid_token.status_code, 401)
        self.assertEqual(res_invalid_token.json()["detail"], "Token invalide")

        res_no_header = self.client.get("/notifications")
        self.assertIn(res_no_header.status_code, (401, 403))

    # 2. USER sans permission notification.read -> 403
    def test_user_without_read_permission_returns_403(self):
        user_no_perm = _user(10, permissions=[])
        self._override_user(user_no_perm)

        res_list = self.client.get("/notifications")
        self.assertEqual(res_list.status_code, 403)

        res_count = self.client.get("/notifications/unread-count")
        self.assertEqual(res_count.status_code, 403)

    # 3. USER sans permission notification.mark_read -> 403
    def test_user_without_mark_read_permission_returns_403(self):
        user_no_perm = _user(10, permissions=[PERMISSION_NOTIFICATION_READ])
        self._override_user(user_no_perm)

        notif = Notification(recipient_user_id=10, action="act", title="T", message="M")
        notification_repository.create(self.db, notif, auto_commit=True)

        res_read = self.client.patch(f"/notifications/{notif.id}/read")
        self.assertEqual(res_read.status_code, 403)

        res_read_all = self.client.patch("/notifications/read-all")
        self.assertEqual(res_read_all.status_code, 403)

    # 4. USER avec notification.read peut lister et filtre strict par destinataire
    def test_user_can_list_own_notifications_and_isolation(self):
        user_1 = _user(1, permissions=[PERMISSION_NOTIFICATION_READ])
        user_2 = _user(2, permissions=[PERMISSION_NOTIFICATION_READ])

        n1 = Notification(recipient_user_id=1, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=2, action="act2", title="T2", message="M2")
        notification_repository.create_many(self.db, [n1, n2], auto_commit=True)

        self._override_user(user_1)
        res = self.client.get("/notifications")
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], n1.id)
        self.assertEqual(data[0]["recipient_user_id"], 1)
        self.assertEqual(data[0]["action"], "act1")
        self.assertEqual(data[0]["title"], "T1")
        self.assertEqual(data[0]["message"], "M1")

    # 5. Pagination limit/offset
    def test_list_notifications_pagination(self):
        user = _user(5, permissions=[PERMISSION_NOTIFICATION_READ])
        self._override_user(user)

        base_time = datetime.now(timezone.utc)
        notifs = [
            Notification(
                recipient_user_id=5,
                action=f"act_{i}",
                title=f"T_{i}",
                message=f"M_{i}",
                created_at=base_time + timedelta(seconds=i),
            )
            for i in range(5)
        ]
        notification_repository.create_many(self.db, notifs, auto_commit=True)

        res_p1 = self.client.get("/notifications?limit=2&offset=0")
        self.assertEqual(res_p1.status_code, 200)
        data_p1 = res_p1.json()
        self.assertEqual(len(data_p1), 2)
        self.assertEqual(data_p1[0]["action"], "act_4")
        self.assertEqual(data_p1[1]["action"], "act_3")

        res_p2 = self.client.get("/notifications?limit=2&offset=2")
        self.assertEqual(res_p2.status_code, 200)
        data_p2 = res_p2.json()
        self.assertEqual(len(data_p2), 2)
        self.assertEqual(data_p2[0]["action"], "act_2")
        self.assertEqual(data_p2[1]["action"], "act_1")

    # 6. Filtre unread_only
    def test_list_notifications_unread_only(self):
        user = _user(6, permissions=[PERMISSION_NOTIFICATION_READ])
        self._override_user(user)

        n1 = Notification(recipient_user_id=6, action="a1", title="T1", message="M1")
        n2 = Notification(
            recipient_user_id=6,
            action="a2",
            title="T2",
            message="M2",
            read_at=datetime.now(timezone.utc),
        )
        notification_repository.create_many(self.db, [n1, n2], auto_commit=True)

        res = self.client.get("/notifications?unread_only=true")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], n1.id)

    # 7. unread-count
    def test_unread_count_endpoint(self):
        user = _user(7, permissions=[PERMISSION_NOTIFICATION_READ])
        self._override_user(user)

        n1 = Notification(recipient_user_id=7, action="a1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=7, action="a2", title="T2", message="M2")
        n3 = Notification(
            recipient_user_id=7,
            action="a3",
            title="T3",
            message="M3",
            read_at=datetime.now(timezone.utc),
        )
        notification_repository.create_many(self.db, [n1, n2, n3], auto_commit=True)

        res = self.client.get("/notifications/unread-count")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"unread_count": 2})

    # 8. Mark notification as read
    def test_user_can_mark_own_notification_as_read(self):
        user = _user(8, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])
        self._override_user(user)

        n1 = Notification(recipient_user_id=8, action="a1", title="T1", message="M1")
        notification_repository.create(self.db, n1, auto_commit=True)

        res = self.client.patch(f"/notifications/{n1.id}/read")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], n1.id)
        self.assertIsNotNone(data["read_at"])

        res_count = self.client.get("/notifications/unread-count")
        self.assertEqual(res_count.json()["unread_count"], 0)

    # 9. USER ne peut pas marquer la notification d'un autre USER (403)
    def test_user_cannot_mark_other_user_notification_as_read(self):
        user_1 = _user(1, permissions=[PERMISSION_NOTIFICATION_MARK_READ])
        user_2 = _user(2, permissions=[PERMISSION_NOTIFICATION_MARK_READ])

        notif_user_2 = Notification(recipient_user_id=2, action="a1", title="T1", message="M1")
        notification_repository.create(self.db, notif_user_2, auto_commit=True)

        self._override_user(user_1)
        res = self.client.patch(f"/notifications/{notif_user_2.id}/read")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["detail"], "Acces interdit a cette notification.")

    # 10. Notification 404 introuvable
    def test_mark_non_existent_notification_returns_404(self):
        user = _user(1, permissions=[PERMISSION_NOTIFICATION_MARK_READ])
        self._override_user(user)

        res = self.client.patch("/notifications/9999/read")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["detail"], "Notification introuvable")

    # 11. read-all isole strictly le propriétaire
    def test_read_all_only_affects_owner(self):
        user_1 = _user(1, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])
        user_2 = _user(2, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])

        n1_u1 = Notification(recipient_user_id=1, action="a1", title="T1", message="M1")
        n2_u1 = Notification(recipient_user_id=1, action="a2", title="T2", message="M2")
        n1_u2 = Notification(recipient_user_id=2, action="a3", title="T3", message="M3")
        notification_repository.create_many(self.db, [n1_u1, n2_u1, n1_u2], auto_commit=True)

        self._override_user(user_1)
        res = self.client.patch("/notifications/read-all")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["updated_count"], 2)

        # Verif user 1
        res_count_1 = self.client.get("/notifications/unread-count")
        self.assertEqual(res_count_1.json()["unread_count"], 0)

        # Verif user 2 (toujours 1 non lue)
        self._override_user(user_2)
        res_count_2 = self.client.get("/notifications/unread-count")
        self.assertEqual(res_count_2.json()["unread_count"], 1)

    # 12. ADMIN avec permissions appropriées peut utiliser ses propres notifications
    def test_admin_uses_own_notifications(self):
        admin = _user(100, role=USER_ROLE_ADMIN, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])
        self._override_user(admin)

        n_admin = Notification(recipient_user_id=100, action="a_admin", title="TA", message="MA")
        n_other = Notification(recipient_user_id=200, action="a_other", title="TO", message="MO")
        notification_repository.create_many(self.db, [n_admin, n_other], auto_commit=True)

        res_list = self.client.get("/notifications")
        self.assertEqual(res_list.status_code, 200)
        data = res_list.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], n_admin.id)

        res_count = self.client.get("/notifications/unread-count")
        self.assertEqual(res_count.json()["unread_count"], 1)

    # 13. Validation des bornes limit / offset
    def test_invalid_query_params_returns_422(self):
        user = _user(1, permissions=[PERMISSION_NOTIFICATION_READ])
        self._override_user(user)

        res_limit_zero = self.client.get("/notifications?limit=0")
        self.assertEqual(res_limit_zero.status_code, 422)

        res_limit_too_high = self.client.get("/notifications?limit=101")
        self.assertEqual(res_limit_too_high.status_code, 422)

        res_offset_negative = self.client.get("/notifications?offset=-1")
        self.assertEqual(res_offset_negative.status_code, 422)


if __name__ == "__main__":
    unittest.main()
