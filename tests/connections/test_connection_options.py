import unittest

from src.masoniteorm.connections.MSSQLConnection import MSSQLConnection
from src.masoniteorm.connections.PostgresConnection import PostgresConnection
from src.masoniteorm.connections.SQLiteConnection import SQLiteConnection


class TestPostgresConnectKwargs(unittest.TestCase):
    def get_connection(self, options=None, full_details=None):
        return PostgresConnection(
            host="localhost",
            database="orm",
            user="postgres",
            port="5432",
            password="secret",
            options=options or {},
            full_details=full_details or {},
        )

    def test_base_kwargs_without_options(self):
        kwargs = self.get_connection()._build_connect_kwargs()
        self.assertEqual(
            kwargs,
            {
                "database": "orm",
                "user": "postgres",
                "password": "secret",
                "host": "localhost",
                "port": 5432,
            },
        )

    def test_known_kwargs_pass_through(self):
        kwargs = self.get_connection(
            options={
                "sslmode": "require",
                "connect_timeout": 10,
                "application_name": "masonite",
            }
        )._build_connect_kwargs()
        self.assertEqual(kwargs["sslmode"], "require")
        self.assertEqual(kwargs["connect_timeout"], 10)
        self.assertEqual(kwargs["application_name"], "masonite")
        self.assertNotIn("options", kwargs)

    def test_unknown_options_become_guc_params(self):
        kwargs = self.get_connection(
            options={"statement_timeout": 5000}
        )._build_connect_kwargs()
        self.assertEqual(kwargs["options"], "-c statement_timeout=5000")

    def test_schema_becomes_search_path(self):
        connection = self.get_connection(full_details={"schema": "tenant"})
        kwargs = connection._build_connect_kwargs()
        self.assertEqual(kwargs["options"], "-c search_path=tenant")

    def test_explicit_search_path_overrides_schema(self):
        connection = self.get_connection(
            options={"search_path": "custom"},
            full_details={"schema": "tenant"},
        )
        kwargs = connection._build_connect_kwargs()
        self.assertEqual(kwargs["options"], "-c search_path=custom")

    def test_async_is_not_passed_through(self):
        kwargs = self.get_connection(
            options={"async": 1}
        )._build_connect_kwargs()
        # "async" is not a supported pass-through kwarg; it must not be
        # injected as a psycopg2 connect kwarg.
        self.assertNotIn("async", kwargs)


class TestSQLiteConnectKwargs(unittest.TestCase):
    def get_connection(self, options=None):
        return SQLiteConnection(
            database="orm.sqlite3",
            options=options or {},
            full_details={},
        )

    def test_no_options(self):
        connect_kwargs, pragmas = self.get_connection()._build_connect_kwargs()
        self.assertEqual(connect_kwargs, {})
        self.assertEqual(pragmas, {})

    def test_known_kwargs_pass_through(self):
        connect_kwargs, pragmas = self.get_connection(
            options={"timeout": 30, "check_same_thread": False}
        )._build_connect_kwargs()
        self.assertEqual(
            connect_kwargs, {"timeout": 30, "check_same_thread": False}
        )
        self.assertEqual(pragmas, {})

    def test_unknown_options_become_pragmas(self):
        connect_kwargs, pragmas = self.get_connection(
            options={"journal_mode": "WAL", "synchronous": "NORMAL"}
        )._build_connect_kwargs()
        self.assertEqual(connect_kwargs, {})
        self.assertEqual(
            pragmas, {"journal_mode": "WAL", "synchronous": "NORMAL"}
        )

    def test_invalid_pragma_name_raises(self):
        with self.assertRaises(ValueError):
            self.get_connection(
                options={"journal mode; DROP TABLE": "WAL"}
            )._build_connect_kwargs()

    def test_pragmas_are_applied_on_connect(self):
        connection = SQLiteConnection(
            database=":memory:",
            options={"journal_mode": "MEMORY"},
            full_details={},
        )
        connection.make_connection()
        result = connection._connection.execute("PRAGMA journal_mode").fetchone()
        self.assertEqual(result[0].lower(), "memory")

    def test_custom_isolation_level_is_respected(self):
        connection = SQLiteConnection(
            database=":memory:",
            options={"isolation_level": "DEFERRED"},
            full_details={},
        )
        connection.make_connection()
        self.assertEqual(connection._connection.isolation_level, "DEFERRED")


class TestMSSQLConnectionString(unittest.TestCase):
    def get_connection(self, options=None, port="1433"):
        return MSSQLConnection(
            host="localhost",
            database="orm",
            user="sa",
            port=port,
            password="secret",
            options=options or {},
            full_details={},
        )

    def test_default_connection_string(self):
        connection_string = self.get_connection()._build_connection_string()
        self.assertEqual(
            connection_string,
            "DRIVER=ODBC Driver 17 for SQL Server;SERVER=localhost,1433;"
            "Connection Timeout=30;DATABASE=orm;UID=sa;PWD=secret",
        )

    def test_known_options(self):
        connection_string = self.get_connection(
            options={
                "driver": "ODBC Driver 18 for SQL Server",
                "connection_timeout": 5,
                "instance": "SQLEXPRESS",
                "trusted_connection": "yes",
                "authentication": "ActiveDirectoryPassword",
                "integrated_security": "SSPI",
            }
        )._build_connection_string()
        self.assertIn("DRIVER=ODBC Driver 18 for SQL Server", connection_string)
        self.assertIn("SERVER=localhost\\SQLEXPRESS,1433", connection_string)
        self.assertIn("Connection Timeout=5", connection_string)
        self.assertIn("Integrated Security=SSPI", connection_string)
        self.assertIn("Trusted_Connection=yes", connection_string)
        self.assertIn("Authentication=ActiveDirectoryPassword", connection_string)

    def test_extra_options_appended_verbatim(self):
        connection_string = self.get_connection(
            options={"Encrypt": "yes", "TrustServerCertificate": "no"}
        )._build_connection_string()
        self.assertIn("Encrypt=yes", connection_string)
        self.assertIn("TrustServerCertificate=no", connection_string)

    def test_port_omitted_when_not_set(self):
        connection_string = self.get_connection(
            port=None
        )._build_connection_string()
        self.assertIn("SERVER=localhost;", connection_string)
        self.assertNotIn(",None", connection_string)
