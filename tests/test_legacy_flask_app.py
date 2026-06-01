import importlib
import importlib.util
import unittest


@unittest.skipIf(importlib.util.find_spec("flask") is None, "flask is not installed")
class TestLegacyFlaskApp(unittest.TestCase):
    def test_import_does_not_create_database_connection(self):
        legacy_app = importlib.import_module("app")

        self.assertIsNone(legacy_app.db)


if __name__ == "__main__":
    unittest.main()
