import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.audit_log import AuditLog
from app.models.user import User, USER_ROLE_ADMIN, USER_ROLE_USER
from app.models.bureau import Bureau
from app.models.circonscription import Circonscription
from app.models.document import Document
from app.models.permission_request import PermissionRequest, PERMISSION_REQUEST_STATUS_PENDING
from app.repositories.audit_log_repository import audit_log_repository
from app.services.audit_log_service import audit_log_service, sanitize_sensitive_data


class TestAuditLogInfrastructure(unittest.TestCase):

    def setUp(self):
        # Utilisation d'une base SQLite en mémoire pour tester le cycle de vie SQLAlchemy
        self.engine = create_engine("sqlite:///:memory:")
        AuditLog.__table__.create(bind=self.engine)

        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    # A. CRÉATION
    def test_audit_log_creation_and_fields(self):
        log = audit_log_service.log_event(
            db=self.db,
            action="document.create",
            entity_type="Document",
            entity_id=101,
            auto_commit=True,
        )

        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.created_at)
        self.assertEqual(log.action, "document.create")
        self.assertEqual(log.entity_type, "Document")
        self.assertEqual(log.entity_id, 101)

    # B. RELATIONS
    def test_audit_log_foreign_key_relations(self):
        log = audit_log_service.log_event(
            db=self.db,
            action="permission.approve",
            entity_type="PermissionRequest",
            entity_id=1,
            actor_user_id=5,
            document_id=10,
            permission_request_id=1,
            bureau_id=2,
            circonscription_id=3,
            auto_commit=True,
        )

        fetched = audit_log_service.get_by_id(self.db, log.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.actor_user_id, 5)
        self.assertEqual(fetched.document_id, 10)
        self.assertEqual(fetched.permission_request_id, 1)
        self.assertEqual(fetched.bureau_id, 2)
        self.assertEqual(fetched.circonscription_id, 3)

    # C. JSONB / STATES / METADATA
    def test_audit_log_json_states_and_metadata(self):
        old_st = {"status": "DRAFT", "title": "Ancien titre"}
        new_st = {"status": "PUBLISHED", "title": "Nouveau titre"}
        meta = {"ip_address": "192.168.1.1", "user_agent": "TestBrowser"}

        log = audit_log_service.log_event(
            db=self.db,
            action="document.update",
            entity_type="Document",
            entity_id=50,
            old_state=old_st,
            new_state=new_st,
            metadata=meta,
            auto_commit=True,
        )

        fetched = audit_log_service.get_by_id(self.db, log.id)
        self.assertEqual(fetched.old_state, old_st)
        self.assertEqual(fetched.new_state, new_st)
        self.assertEqual(fetched.metadata_, meta)

    # D. TRANSACTION ET FLUSH SANS COMMIT FORCÉ
    def test_transaction_flush_without_forced_commit(self):
        log = audit_log_service.log_event(
            db=self.db,
            action="movement.create",
            entity_type="Movement",
            entity_id=20,
            auto_commit=False,  # Comportement par défaut
        )

        # L'identifiant est généré grâce au db.flush() interne
        self.assertIsNotNone(log.id)

        # Si le workflow fait un rollback, le log non commité n'est pas conservé
        self.db.rollback()
        fetched_after_rollback = audit_log_service.get_by_id(self.db, log.id)
        self.assertIsNone(fetched_after_rollback)

        # Re-test avec commit orchestré par le workflow métier
        log2 = audit_log_service.log_event(
            db=self.db,
            action="movement.create",
            entity_type="Movement",
            entity_id=21,
            auto_commit=False,
        )
        self.assertIsNotNone(log2.id)
        self.db.commit()

        fetched_after_commit = audit_log_service.get_by_id(self.db, log2.id)
        self.assertIsNotNone(fetched_after_commit)

    # E. EXPURGATION DES DONNÉES SENSIBLES
    def test_sensitive_data_sanitization(self):
        sensitive_payload = {
            "password": "secret_password_123",
            "mot_de_passe": "autre_secret",
            "token": "token_abc_xyz",
            "access_token": "access_token_val",
            "refresh_token": "refresh_token_val",
            "jwt": "bearer_jwt_string",
            "secret": "top_secret",
            "authorization": "Bearer xxx.yyy.zzz",
            "file_content": "binary_content_bytes",
            "nested": {
                "password": "nested_password",
                "normal_field": "valeur_normale",
            },
            "list_data": [
                {"jwt": "jwt_in_list"},
                "item_normal",
            ],
        }

        sanitized = sanitize_sensitive_data(sensitive_payload)

        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["mot_de_passe"], "[REDACTED]")
        self.assertEqual(sanitized["token"], "[REDACTED]")
        self.assertEqual(sanitized["access_token"], "[REDACTED]")
        self.assertEqual(sanitized["refresh_token"], "[REDACTED]")
        self.assertEqual(sanitized["jwt"], "[REDACTED]")
        self.assertEqual(sanitized["secret"], "[REDACTED]")
        self.assertEqual(sanitized["authorization"], "[REDACTED]")
        self.assertEqual(sanitized["file_content"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["password"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["normal_field"], "valeur_normale")
        self.assertEqual(sanitized["list_data"][0]["jwt"], "[REDACTED]")
        self.assertEqual(sanitized["list_data"][1], "item_normal")

        log = audit_log_service.log_event(
            db=self.db,
            action="user.login",
            entity_type="User",
            entity_id=1,
            old_state=sensitive_payload,
            metadata=sensitive_payload,
            auto_commit=True,
        )

        self.assertEqual(log.old_state["password"], "[REDACTED]")
        self.assertEqual(log.metadata_["token"], "[REDACTED]")

    # F. IMMUTABILITÉ APPLICATIVE
    def test_immutability_no_update_or_delete_methods(self):
        # Vérification qu'aucune méthode update/delete n'est exposée sur le repo ou service
        for obj in (audit_log_repository, audit_log_service):
            methods = [m for m in dir(obj) if not m.startswith("_")]
            for method in methods:
                self.assertNotIn("update", method.lower())
                self.assertNotIn("delete", method.lower())
                self.assertNotIn("remove", method.lower())

    # G. ISOLATION ET RECHERCHES PAR SCOPE
    def test_list_logs_filtering_by_scope(self):
        # Inscription de logs pour des contextes différents
        audit_log_service.log_event(
            db=self.db,
            action="doc.read",
            entity_type="Document",
            entity_id=1,
            actor_user_id=10,
            bureau_id=100,
            circonscription_id=1000,
            auto_commit=True,
        )
        audit_log_service.log_event(
            db=self.db,
            action="doc.read",
            entity_type="Document",
            entity_id=2,
            actor_user_id=20,
            bureau_id=200,
            circonscription_id=1000,
            auto_commit=True,
        )
        audit_log_service.log_event(
            db=self.db,
            action="doc.write",
            entity_type="Document",
            entity_id=3,
            actor_user_id=10,
            bureau_id=100,
            circonscription_id=2000,
            auto_commit=True,
        )

        logs_user_10 = audit_log_service.list_logs(self.db, actor_user_id=10)
        self.assertEqual(len(logs_user_10), 2)

        logs_circ_1000 = audit_log_service.list_logs(self.db, circonscription_id=1000)
        self.assertEqual(len(logs_circ_1000), 2)

        logs_bureau_200 = audit_log_service.list_logs(self.db, bureau_id=200)
        self.assertEqual(len(logs_bureau_200), 1)

    # VERIFICATION DE VALIDATION DE L'ACTION ET ENTITY_TYPE
    def test_log_event_requires_action_and_entity_type(self):
        with self.assertRaises(ValueError):
            audit_log_service.log_event(self.db, action="", entity_type="Document")

        with self.assertRaises(ValueError):
            audit_log_service.log_event(self.db, action="doc.read", entity_type="   ")
