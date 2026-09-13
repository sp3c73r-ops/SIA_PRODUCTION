from datetime import datetime, timezone
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.notification import Notification


class TestNotificationModel(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Notification.__table__.create(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    def test_notification_creation_and_defaults(self):
        notif = Notification(
            recipient_user_id=1,
            action="permission_request.created",
            title="Nouvelle demande",
            message="Message de test",
            permission_request_id=10,
            document_id=5,
            bureau_id=2,
            circonscription_id=100,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.recipient_user_id, 1)
        self.assertEqual(notif.action, "permission_request.created")
        self.assertEqual(notif.title, "Nouvelle demande")
        self.assertEqual(notif.message, "Message de test")
        self.assertEqual(notif.permission_request_id, 10)
        self.assertEqual(notif.document_id, 5)
        self.assertEqual(notif.bureau_id, 2)
        self.assertEqual(notif.circonscription_id, 100)
        self.assertIsNone(notif.read_at)  # Statut non lu par défaut (read_at IS NULL)
        self.assertIsNotNone(notif.created_at)

    def test_notification_mark_as_read(self):
        notif = Notification(
            recipient_user_id=1,
            action="permission_request.approved",
            title="Demande approuvee",
            message="Votre demande a ete approuvee",
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        # Non lue
        self.assertIsNone(notif.read_at)

        # Marquage comme lue
        now = datetime.now(timezone.utc)
        notif.read_at = now
        self.db.commit()
        self.db.refresh(notif)

        self.assertIsNotNone(notif.read_at)
