import unittest
from unittest.mock import patch, sentinel

from src.mock_generator.writer_selector import get_writer


class WriterSelectorTests(unittest.TestCase):
    @patch("src.mock_generator.writer_selector.import_module")
    def test_mysql_writer_is_selected(self, import_module):
        import_module.return_value = sentinel.writer
        self.assertIs(get_writer("MYSQL"), sentinel.writer)
        import_module.assert_called_once_with("src.load.mysql_writer")

    @patch("src.mock_generator.writer_selector.import_module")
    def test_postgres_writer_is_selected(self, import_module):
        import_module.return_value = sentinel.writer
        self.assertIs(get_writer(" postgres "), sentinel.writer)
        import_module.assert_called_once_with("src.load.postgres_writer")

    def test_unknown_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Geçersiz MOCK_TARGET"):
            get_writer("oracle")


if __name__ == "__main__":
    unittest.main()
