import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.notification import Notification
from app.repositories.notification_repository import notification_repository


class TestNotificationRepository(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Notification.__table__.create(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    def test_create_auto_commit_true(self):
        notif = Notification(
            recipient_user_id=10,
            action="perm.created",
            title="Titre",
            message="Message",
        )
        saved = notification_repository.create(self.db, notif, auto_commit=True)
        self.assertIsNotNone(saved.id)

        fetched = notification_repository.get_by_id(self.db, saved.id)
        self.assertIsNotNone(fetched)

    def test_create_auto_commit_false_flush_only(self):
        notif = Notification(
            recipient_user_id=10,
            action="perm.created",
            title="Titre",
            message="Message",
        )
        saved = notification_repository.create(self.db, notif, auto_commit=False)
        self.assertIsNotNone(saved.id)

        # Avant commit
        self.db.rollback()
        fetched = notification_repository.get_by_id(self.db, saved.id)
        self.assertIsNone(fetched)

    def test_create_many(self):
        notifs = [
            Notification(recipient_user_id=1, action="act1", title="T1", message="M1"),
            Notification(recipient_user_id=2, action="act2", title="T2", message="M2"),
        ]
        saved_list = notification_repository.create_many(self.db, notifs, auto_commit=True)
        self.assertEqual(len(saved_list), 2)
        self.assertIsNotNone(saved_list[0].id)
        self.assertIsNotNone(saved_list[1].id)

    # 7. AUTO_COMMIT=False — CREATE_MANY
    def test_create_many_auto_commit_false_rollback(self):
        notifs = [
            Notification(recipient_user_id=10, action="act1", title="T1", message="M1"),
            Notification(recipient_user_id=10, action="act2", title="T2", message="M2"),
        ]
        saved_list = notification_repository.create_many(self.db, notifs, auto_commit=False)
        self.assertEqual(len(saved_list), 2)
        id1, id2 = saved_list[0].id, saved_list[1].id
        self.assertIsNotNone(id1)

        self.db.rollback()
        self.assertIsNone(notification_repository.get_by_id(self.db, id1))
        self.assertIsNone(notification_repository.get_by_id(self.db, id2))

    def test_list_for_recipient_and_unread_filter(self):
        notif1 = Notification(recipient_user_id=5, action="act1", title="T1", message="M1")
        notif2 = Notification(recipient_user_id=5, action="act2", title="T2", message="M2", read_at=datetime.now(timezone.utc))
        notif3 = Notification(recipient_user_id=9, action="act3", title="T3", message="M3")

        notification_repository.create_many(self.db, [notif1, notif2, notif3], auto_commit=True)

        all_user_5 = notification_repository.list_for_recipient(self.db, recipient_user_id=5, unread_only=False)
        self.assertEqual(len(all_user_5), 2)

        unread_user_5 = notification_repository.list_for_recipient(self.db, recipient_user_id=5, unread_only=True)
        self.assertEqual(len(unread_user_5), 1)
        self.assertEqual(unread_user_5[0].id, notif1.id)

    def test_count_unread_for_recipient(self):
        notif1 = Notification(recipient_user_id=7, action="act1", title="T1", message="M1")
        notif2 = Notification(recipient_user_id=7, action="act2", title="T2", message="M2")
        notif3 = Notification(recipient_user_id=7, action="act3", title="T3", message="M3", read_at=datetime.now(timezone.utc))

        notification_repository.create_many(self.db, [notif1, notif2, notif3], auto_commit=True)

        count = notification_repository.count_unread_for_recipient(self.db, recipient_user_id=7)
        self.assertEqual(count, 2)

    def test_mark_as_read(self):
        notif = Notification(recipient_user_id=8, action="act1", title="T1", message="M1")
        notification_repository.create(self.db, notif, auto_commit=True)

        self.assertIsNone(notif.read_at)

        success = notification_repository.mark_as_read(self.db, notif.id, recipient_user_id=8, auto_commit=True)
        self.assertTrue(success)

        fetched = notification_repository.get_by_id(self.db, notif.id)
        self.assertIsNotNone(fetched.read_at)

        # Tentative répétée sur déjà lu -> False
        success_second = notification_repository.mark_as_read(self.db, notif.id, recipient_user_id=8, auto_commit=True)
        self.assertFalse(success_second)

        # Tentative par un autre utilisateur -> False
        success_other = notification_repository.mark_as_read(self.db, notif.id, recipient_user_id=99, auto_commit=True)
        self.assertFalse(success_other)

    # 5. AUTO_COMMIT=False — MARK AS READ
    def test_mark_as_read_auto_commit_false(self):
        notif = Notification(recipient_user_id=8, action="act1", title="T1", message="M1")
        notification_repository.create(self.db, notif, auto_commit=True)
        self.assertIsNone(notif.read_at)

        success = notification_repository.mark_as_read(self.db, notif.id, recipient_user_id=8, auto_commit=False)
        self.assertTrue(success)

        # Dans la transaction courante, le décompte non lu devient 0 (flush SQL effectué)
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, 8), 0)

        # Après rollback, le décompte non lu redevient 1
        self.db.rollback()
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, 8), 1)

    def test_mark_all_as_read(self):
        n1 = Notification(recipient_user_id=12, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=12, action="act2", title="T2", message="M2")
        n3 = Notification(recipient_user_id=12, action="act3", title="T3", message="M3", read_at=datetime.now(timezone.utc))
        notification_repository.create_many(self.db, [n1, n2, n3], auto_commit=True)

        updated_count = notification_repository.mark_all_as_read(self.db, recipient_user_id=12, auto_commit=True)
        self.assertEqual(updated_count, 2)

        unread_count = notification_repository.count_unread_for_recipient(self.db, recipient_user_id=12)
        self.assertEqual(unread_count, 0)

    # 6. AUTO_COMMIT=False — MARK ALL AS READ
    def test_mark_all_as_read_auto_commit_false(self):
        n1 = Notification(recipient_user_id=12, action="act1", title="T1", message="M1")
        n2 = Notification(recipient_user_id=12, action="act2", title="T2", message="M2")
        notification_repository.create_many(self.db, [n1, n2], auto_commit=True)

        updated_count = notification_repository.mark_all_as_read(self.db, recipient_user_id=12, auto_commit=False)
        self.assertEqual(updated_count, 2)

        # Dans la transaction, 0 non lues
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, recipient_user_id=12), 0)

        # Après rollback, 2 non lues à nouveau
        self.db.rollback()
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, recipient_user_id=12), 2)

    # 10. MARK_ALL AS READ — ISOLATION
    def test_mark_all_as_read_isolation_between_recipients(self):
        n_a1 = Notification(recipient_user_id=100, action="act1", title="T1", message="M1")
        n_a2 = Notification(recipient_user_id=100, action="act2", title="T2", message="M2")
        n_b1 = Notification(recipient_user_id=200, action="act3", title="T3", message="M3")
        n_b2 = Notification(recipient_user_id=200, action="act4", title="T4", message="M4")
        notification_repository.create_many(self.db, [n_a1, n_a2, n_b1, n_b2], auto_commit=True)

        updated = notification_repository.mark_all_as_read(self.db, recipient_user_id=100, auto_commit=True)
        self.assertEqual(updated, 2)

        # USER A a 0 non lues, USER B conserve 2 non lues
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, recipient_user_id=100), 0)
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, recipient_user_id=200), 2)

    # 8. PAGINATION
    def test_list_for_recipient_pagination_and_ordering(self):
        base_time = datetime.now(timezone.utc)
        notifs = []
        for i in range(5):
            notifs.append(
                Notification(
                    recipient_user_id=50,
                    action=f"act_{i}",
                    title=f"Title {i}",
                    message=f"Msg {i}",
                    created_at=base_time + timedelta(seconds=i),
                )
            )
        # Notification d'un autre destinataire qui ne doit jamais apparaître
        other_notif = Notification(
            recipient_user_id=99,
            action="other_act",
            title="Other Title",
            message="Other Msg",
            created_at=base_time + timedelta(seconds=10),
        )

        notification_repository.create_many(self.db, notifs + [other_notif], auto_commit=True)

        # Page 1: limit=2, offset=0 -> doit ramener act_4 et act_3 (plus récentes)
        page1 = notification_repository.list_for_recipient(self.db, recipient_user_id=50, limit=2, offset=0)
        self.assertEqual(len(page1), 2)
        self.assertEqual(page1[0].action, "act_4")
        self.assertEqual(page1[1].action, "act_3")
        self.assertTrue(all(n.recipient_user_id == 50 for n in page1))

        # Page 2: limit=2, offset=2 -> doit ramener act_2 et act_1
        page2 = notification_repository.list_for_recipient(self.db, recipient_user_id=50, limit=2, offset=2)
        self.assertEqual(len(page2), 2)
        self.assertEqual(page2[0].action, "act_2")
        self.assertEqual(page2[1].action, "act_1")

        # Page 3: limit=2, offset=4 -> doit ramener act_0
        page3 = notification_repository.list_for_recipient(self.db, recipient_user_id=50, limit=2, offset=4)
        self.assertEqual(len(page3), 1)
        self.assertEqual(page3[0].action, "act_0")

    # 9. UNREAD_ONLY + PAGINATION
    def test_list_for_recipient_unread_only_pagination(self):
        base_time = datetime.now(timezone.utc)
        notifs = []
        for i in range(6):
            # i = 0, 2, 4 non lues ; i = 1, 3, 5 lues
            read_at_val = datetime.now(timezone.utc) if i % 2 == 1 else None
            notifs.append(
                Notification(
                    recipient_user_id=60,
                    action=f"act_{i}",
                    title=f"Title {i}",
                    message=f"Msg {i}",
                    read_at=read_at_val,
                    created_at=base_time + timedelta(seconds=i),
                )
            )

        notification_repository.create_many(self.db, notifs, auto_commit=True)

        # Unread limit=2, offset=0 -> doit ramener act_4 puis act_2
        page1_unread = notification_repository.list_for_recipient(
            self.db, recipient_user_id=60, limit=2, offset=0, unread_only=True
        )
        self.assertEqual(len(page1_unread), 2)
        self.assertEqual(page1_unread[0].action, "act_4")
        self.assertEqual(page1_unread[1].action, "act_2")

        # Unread limit=2, offset=2 -> doit ramener act_0
        page2_unread = notification_repository.list_for_recipient(
            self.db, recipient_user_id=60, limit=2, offset=2, unread_only=True
        )
        self.assertEqual(len(page2_unread), 1)
        self.assertEqual(page2_unread[0].action, "act_0")

    # 13. TRANSACTION CREATE + ROLLBACK
    def test_create_auto_commit_false_rollback(self):
        notif = Notification(recipient_user_id=70, action="act_test", title="T", message="M")
        notification_repository.create(self.db, notif, auto_commit=False)

        self.db.rollback()
        self.assertEqual(notification_repository.count_unread_for_recipient(self.db, 70), 0)
