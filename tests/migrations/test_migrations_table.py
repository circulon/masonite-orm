import unittest

from src.masoniteorm.connections import ConnectionFactory
from src.masoniteorm.migrations import Migration
from src.masoniteorm.schema import Schema
from src.masoniteorm.schema.platforms import SQLitePlatform
from tests.integrations.config.database import DB


class TestMigrationsTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection = ConnectionFactory().make("sqlite")
        cls.schema = Schema(
            connection="dev",
            connection_class=cls.connection,
            connection_details=DB.get_connection_details(),
            platform=SQLitePlatform,
        )

        cls.schema.drop_table_if_exists("migrations")

    def test_can_create_migrations_table(self):
        self.assertFalse(self.schema.has_table("migrations"))

        migration = Migration(connection="dev")
        migration.create_table_if_not_exists()

        self.assertTrue(self.schema.has_table("migrations"))

    def test_can_create_table_with_id_against_real_database(self):
        # Executes the generated DDL so an invalid AUTOINCREMENT definition
        # cannot slip through the string-based schema tests.
        self.schema.drop_table_if_exists("id_pk_test")

        with self.schema.create("id_pk_test") as table:
            table.id()
            table.string("name")

        self.assertTrue(self.schema.has_table("id_pk_test"))
        self.schema.drop_table_if_exists("id_pk_test")
