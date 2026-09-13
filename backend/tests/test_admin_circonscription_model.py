import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import configure_mappers

from app.models.circonscription import Circonscription
from app.models.user import User


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "6c2f4a8e1d90_add_admin_circonscription_to_users.py"
)


def _migration_module():
    specification = importlib.util.spec_from_file_location(
        "admin_circonscription_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class TestAdminCirconscriptionModel(unittest.TestCase):

    def test_admin_circonscription_column_is_nullable_restrict_fk(self):
        column = User.__table__.c.admin_circonscription_id

        self.assertTrue(column.nullable)
        self.assertEqual(
            next(iter(column.foreign_keys)).target_fullname,
            "circonscriptions.id",
        )
        self.assertEqual(next(iter(column.foreign_keys)).ondelete, "RESTRICT")

    def test_admin_circonscription_relationships_are_bidirectional(self):
        configure_mappers()

        self.assertEqual(
            User.admin_circonscription.property.mapper.class_,
            Circonscription,
        )
        self.assertEqual(
            Circonscription.admins.property.mapper.class_,
            User,
        )
        self.assertEqual(User.admin_circonscription.property.back_populates, "admins")
        self.assertEqual(Circonscription.admins.property.back_populates, "admin_circonscription")

    def test_user_allows_null_admin_circonscription_during_transition(self):
        user = User(admin_circonscription_id=None)

        self.assertIsNone(user.admin_circonscription_id)

    def test_migration_prepares_partial_unique_index(self):
        module = _migration_module()
        operations = MagicMock()

        with patch.object(module, "op", operations):
            module.upgrade()

        self.assertEqual(module.revision, "6c2f4a8e1d90")
        self.assertEqual(module.down_revision, "0a7d3b4c9e20")
        operations.create_index.assert_any_call(
            "uq_users_one_admin_per_circonscription",
            "users",
            ["admin_circonscription_id"],
            unique=True,
            postgresql_where=unittest.mock.ANY,
        )

    def test_migration_downgrade_removes_prepared_indexes_and_fk(self):
        module = _migration_module()
        operations = MagicMock()

        with patch.object(module, "op", operations):
            module.downgrade()

        operations.drop_index.assert_any_call(
            "uq_users_one_admin_per_circonscription",
            table_name="users",
        )
        operations.drop_constraint.assert_called_once_with(
            "fk_users_admin_circonscription",
            "users",
            type_="foreignkey",
        )