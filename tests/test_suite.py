import unittest
import os
from unittest.mock import MagicMock, patch
from database import Database
from main import DoorLockServer
from vision_ai import VisionAI

class TestDoorlockSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 테스트용 DB를 새로 만든다.
        cls.db_path = "/tmp/doorlock_unit_test.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = Database(db_path=cls.db_path)
        cls.vision = VisionAI(mock=True)
        with patch('serial.Serial'):
            cls.server = DoorLockServer(cls.db, vision=cls.vision)
            cls.server.ser = MagicMock()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_01_user_registration(self):
        print("\n[Test 1] 사용자 등록")
        face_encoding, _ = self.vision.capture_face_encoding()
        user_id = self.db.add_user("TestUser", nfc_uid="TEST1234", password="1111", face_encoding=face_encoding)
        self.assertIsNotNone(user_id)
        print("ok: 사용자 등록됨")

    def test_02_successful_2fa_nfc(self):
        print("\n[Test 2] NFC 통과 경로")
        # 등록된 NFC 입력
        self.server.handle_wakeup("WAKEUP:NFC:TEST1234")
        
        # 마지막 로그가 최종 허용인지 확인한다.
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT status FROM access_logs ORDER BY id DESC LIMIT 1")
        status = cursor.fetchone()[0]
        self.assertEqual(status, "FINAL_SUCCESS")
        print("ok: NFC 경로 통과")

    def test_03_failed_2fa_wrong_pw(self):
        print("\n[Test 3] 잘못된 PIN")
        self.server.last_failed_attempt = 0
        self.server.handle_wakeup("WAKEUP:PW:9999")
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT status FROM access_logs ORDER BY id DESC LIMIT 1")
        status = cursor.fetchone()[0]
        self.assertEqual(status, "UNAUTHORIZED")
        print("ok: 잘못된 PIN 거부")

    def test_04_security_alert_trigger(self):
        print("\n[Test 4] 연속 실패 경고")
        # 연속 실패 상황을 만든다.
        for _ in range(3):
            self.server.last_failed_attempt = 0
            self.server.handle_wakeup("WAKEUP:PW:0000")
        
        self.assertTrue(self.db.has_consecutive_failures(limit=3))
        print("ok: 연속 실패 경고 표시")

if __name__ == "__main__":
    unittest.main()
