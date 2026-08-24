import unittest
import sys
from types import ModuleType
from unittest.mock import Mock, patch

try:
    import psycopg2  # noqa: F401
except ModuleNotFoundError:
    psycopg2_stub = ModuleType("psycopg2")
    psycopg2_stub.connect = Mock()
    extras_stub = ModuleType("psycopg2.extras")
    extras_stub.execute_values = Mock()
    sys.modules["psycopg2"] = psycopg2_stub
    sys.modules["psycopg2.extras"] = extras_stub

try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    dotenv_stub = ModuleType("dotenv")
    dotenv_stub.load_dotenv = Mock()
    sys.modules["dotenv"] = dotenv_stub

from src.load.silver_writer import write_to_silver


class SilverWriterTests(unittest.TestCase):
    @patch("src.load.silver_writer.write_events")
    @patch("src.load.silver_writer.write_orders")
    @patch("src.load.silver_writer._get_connection")
    def test_combined_load_commits_once(self, get_connection, write_orders, write_events):
        conn = Mock()
        get_connection.return_value = conn
        write_to_silver("orders", "events")
        write_orders.assert_called_once_with("orders", conn=conn, commit=False)
        write_events.assert_called_once_with("events", conn=conn, commit=False)
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()
        conn.close.assert_called_once()

    @patch("src.load.silver_writer.write_orders", side_effect=RuntimeError("load failed"))
    @patch("src.load.silver_writer._get_connection")
    def test_combined_load_rolls_back_on_failure(self, get_connection, write_orders):
        conn = Mock()
        get_connection.return_value = conn
        with self.assertRaises(RuntimeError):
            write_to_silver("orders", "events")
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
