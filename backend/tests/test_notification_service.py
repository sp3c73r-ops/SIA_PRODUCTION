from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.notification import Notification
from app.models.user import USER_ROLE_ADMIN, USER_ROLE_USER, User
from app.security.permissions import PERMISSION_NOTIFICATION_MARK_READ, PERMISSION_NOTIFICATION_READ
from app.services.notification_service import notification_service


def _user(user_id: int, role: str, permissions=None, admin_circonscription_id=None):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        admin_circonscription_id=admin_circonscription_id,
    )


class TestNotificationService(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Notification.__table__.create(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    def test_notify_user_validations(self):
        with self.assertRaises(ValueError):
            notification_service.notify_user(self.db, recipient_user_id=0, action="act", title="T", message="M")

        with self.assertRaises(ValueError):
            notification_service.notify_user(self.db, recipient_user_id=1, action="", title="T", message="M")

        with self.assertRaises(ValueError):
            notification_service.notify_user(self.db, recipient_user_id=1, action="act", title=" ", message="M")

        with self.assertRaises(ValueError):
            notification_service.notify_user(self.db, recipient_user_id=1, action="act", title="T", message=" ")

    def test_notify_user_creation(self):
        notif = notification_service.notify_user(
            db=self.db,
            recipient_user_id=10,
            action="perm.created",
            title="Titre de notification",
            message="Message de notification",
            permission_request_id=1,
            document_id=2,
            bureau_id=3,
            circonscription_id=4,
            auto_commit=True,
        )

        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.recipient_user_id, 10)
        self.assertEqual(notif.action, "perm.created")
        self.assertEqual(notif.title, "Titre de notification")
        self.assertEqual(notif.message, "Message de notification")
        self.assertEqual(notif.permission_request_id, 1)
        self.assertEqual(notif.document_id, 2)
        self.assertEqual(notif.bureau_id, 3)
        self.assertEqual(notif.circonscription_id, 4)

    # 1. ISOLATION SERVICE — MARK AS READ
    def test_mark_as_read_isolation_between_users(self):
        user_a = _user(10, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_MARK_READ])
        user_b = _user(20, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_MARK_READ])

        # Création d'une notification appartenant à USER B
        notif_b = Notification(recipient_user_id=20, action="act", title="T", message="M")
        self.db.add(notif_b)
        self.db.commit()

        # USER A tente de marquer comme lue la notification de USER B
        result = notification_service.mark_as_read(self.db, notif_b.id, user_a, auto_commit=True)
        self.assertFalse(result)

        # La notification de USER B reste NON LUE (read_at IS NULL)
        fetched_b = self.db.query(Notification).filter(Notification.id == notif_b.id).first()
        self.assertIsNone(fetched_b.read_at)

    # 2. PERMISSION mark_read
    def test_mark_as_read_requires_permission(self):
        user_no_perm = _user(30, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ])
        notif = Notification(recipient_user_id=30, action="act", title="T", message="M")
        self.db.add(notif)
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            notification_service.mark_as_read(self.db, notif.id, user_no_perm)

        self.assertEqual(ctx.exception.status_code, 403)

    # 3. PERMISSION read POUR LISTING
    def test_list_my_notifications_requires_permission(self):
        user_no_perm = _user(40, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_MARK_READ])

        with self.assertRaises(HTTPException) as ctx:
            notification_service.list_my_notifications(self.db, user_no_perm)

        self.assertEqual(ctx.exception.status_code, 403)

    # 4. PERMISSION read POUR UNREAD COUNT
    def test_count_my_unread_requires_permission(self):
        user_no_perm = _user(50, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_MARK_READ])

        with self.assertRaises(HTTPException) as ctx:
            notification_service.count_my_unread(self.db, user_no_perm)

        self.assertEqual(ctx.exception.status_code, 403)

    # 11. NOTIFY ADMINS — AUCUN ADMIN ACTIF
    def test_notify_admins_no_active_admin(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []

        with patch.object(self.db, "query", return_value=mock_query):
            notifs = notification_service.notify_admins_of_circonscription(
                db=self.db,
                circonscription_id=999,
                action="act",
                title="T",
                message="M",
                auto_commit=True,
            )

        self.assertEqual(notifs, [])

    # 12. NOTIFY ADMINS — ISOLATION CIRCONSCRIPTION
    def test_notify_admins_isolation_circonscription(self):
        admin_circ_100 = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=100)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [admin_circ_100]

        with patch.object(self.db, "query", return_value=mock_query):
            notifs = notification_service.notify_admins_of_circonscription(
                db=self.db,
                circonscription_id=100,
                action="perm.created",
                title="Nouvelle demande",
                message="Message pour admin 100",
                auto_commit=True,
            )

        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0].recipient_user_id, 1)

    def test_notify_admins_of_circonscription(self):
        admin1 = _user(1, USER_ROLE_ADMIN, admin_circonscription_id=100)
        admin2 = _user(2, USER_ROLE_ADMIN, admin_circonscription_id=100)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [admin1, admin2]

        with patch.object(self.db, "query", return_value=mock_query):
            notifs = notification_service.notify_admins_of_circonscription(
                db=self.db,
                circonscription_id=100,
                action="perm.created",
                title="Nouvelle demande",
                message="Message pour admin",
                auto_commit=True,
            )

        self.assertEqual(len(notifs), 2)
        recipients = {n.recipient_user_id for n in notifs}
        self.assertEqual(recipients, {1, 2})

    def test_list_my_notifications_isolation_and_permission(self):
        user_a = _user(10, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ])
        user_b = _user(20, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ])
        user_no_perm = _user(30, USER_ROLE_USER, permissions=[])

        # Création de notifications directes
        n1 = Notification(recipient_user_id=10, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=20, action="act2", title="T2", message="M2")
        self.db.add_all([n1, n2])
        self.db.commit()

        # Succès user_a (voit uniquement n1)
        res_a = notification_service.list_my_notifications(self.db, user_a)
        self.assertEqual(len(res_a), 1)
        self.assertEqual(res_a[0].recipient_user_id, 10)

        # Échec sans permission notification.read
        with self.assertRaises(HTTPException) as ctx:
            notification_service.list_my_notifications(self.db, user_no_perm)

        self.assertEqual(ctx.exception.status_code, 403)

    def test_count_my_unread(self):
        user = _user(15, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ])
        n1 = Notification(recipient_user_id=15, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=15, action="act2", title="T2", message="M2")
        self.db.add_all([n1, n2])
        self.db.commit()

        count = notification_service.count_my_unread(self.db, user)
        self.assertEqual(count, 2)

    def test_mark_as_read(self):
        user = _user(15, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])
        n1 = Notification(recipient_user_id=15, action="act1", title="T1", message="M1")
        self.db.add(n1)
        self.db.commit()

        success = notification_service.mark_as_read(self.db, n1.id, user, auto_commit=True)
        self.assertTrue(success)

        count = notification_service.count_my_unread(self.db, user)
        self.assertEqual(count, 0)

    def test_mark_all_as_read(self):
        user = _user(18, USER_ROLE_USER, permissions=[PERMISSION_NOTIFICATION_READ, PERMISSION_NOTIFICATION_MARK_READ])
        n1 = Notification(recipient_user_id=18, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=18, action="act2", title="T2", message="M2")
        self.db.add_all([n1, n2])
        self.db.commit()

        updated_count = notification_service.mark_all_as_read(self.db, user, auto_commit=True)
        self.assertEqual(updated_count, 2)

        count = notification_service.count_my_unread(self.db, user)
        self.assertEqual(count, 0)
