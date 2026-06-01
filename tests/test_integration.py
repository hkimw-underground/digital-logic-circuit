import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("DOORLOCK_VISION_MOCK", "1")
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

from main import DoorLockServer
from database import Database
from vision_ai import VisionAI

class TestDoorLockIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 통합 테스트에서 공유할 DB를 준비한다.
        cls.db_path = "/tmp/doorlock_integration_test.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = Database(db_path=cls.db_path)
        cls.vision = VisionAI(mock=True)
        face_encoding, _ = cls.vision.capture_face_encoding()
        cls.db.add_user("Admin", nfc_uid="A1B2C3D4", password="1234", face_encoding=face_encoding)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.vision.release()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        with patch('serial.Serial'):
            # 같은 DB를 쓰는 서버 인스턴스를 만든다.
            self.server = DoorLockServer(db=self.db, vision=self.vision)
            self.server.ser = MagicMock()

    def test_successful_2fa_nfc(self):
        print("\nNFC 통과 경로 테스트")
        self.server.handle_wakeup("WAKEUP:NFC:A1B2C3D4")
        self.server.ser.write.assert_called_with(b"OPEN_DOOR\n")
        print("ok")

    def test_successful_2fa_pw(self):
        print("\nPIN 통과 경로 테스트")
        self.server.handle_wakeup("WAKEUP:PW:1234")
        self.server.ser.write.assert_called_with(b"OPEN_DOOR\n")
        print("ok")

    def test_failed_1st_auth(self):
        print("\n등록되지 않은 NFC 테스트")
        self.server.ser.write.reset_mock()
        self.server.handle_wakeup("WAKEUP:NFC:WRONG_UID")
        # Correct behavior: server must explicitly tell Arduino to deny (buzzer, LED)
        self.server.ser.write.assert_called_with(b"AUTH_FAIL\n")
        print("ok")

    def test_failed_2nd_auth(self):
        print("\n얼굴 확인 실패 테스트")
        self.server.ser.write.reset_mock()
        with patch.object(self.server.vision, 'verify_face', return_value=False):
            self.server.handle_wakeup("WAKEUP:NFC:A1B2C3D4")
            self.server.ser.write.assert_called_with(b"AUTH_FAIL\n")
        print("ok")

if __name__ == "__main__":
    unittest.main()
