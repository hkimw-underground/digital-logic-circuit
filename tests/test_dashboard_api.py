import importlib.util
import os
import unittest

from database import Database


@unittest.skipIf(importlib.util.find_spec("fastapi") is None, "fastapi is not installed")
class TestDashboardApiPayload(unittest.TestCase):
    def setUp(self):
        import web_app

        self.web_app = web_app
        self.original_db = self.web_app.db
        self.db_path = "/tmp/doorlock_dashboard_api_test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(db_path=self.db_path)
        self.web_app.configure_services(database=self.db)

    def tearDown(self):
        self.web_app.configure_services(database=self.original_db)
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_logs_payload_includes_server_side_alert_state(self):
        self.db.log_access(None, "PW", "UNAUTHORIZED")
        self.db.log_access(None, "NFC", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "FINAL_FAIL")

        payload = self.web_app.logs_payload()

        self.assertTrue(payload["alert"])
        self.assertEqual(len(payload["logs"]), 3)


if __name__ == "__main__":
    unittest.main()
