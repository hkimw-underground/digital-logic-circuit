import unittest

from validation import RegistrationValidationError, normalize_nfc_uid, validate_registration


class TestRegistrationValidation(unittest.TestCase):
    def test_valid_registration_is_trimmed_and_normalized(self):
        username, nfc_uid, pin = validate_registration(" Alice ", " a1b2c3d4 ", " 1234 ")

        self.assertEqual(username, "Alice")
        self.assertEqual(nfc_uid, "A1B2C3D4")
        self.assertEqual(pin, "1234")

    def test_rejects_non_hex_nfc_uid(self):
        with self.assertRaises(RegistrationValidationError):
            validate_registration("Alice", "TEST1234", "1234")

    def test_rejects_non_numeric_pin(self):
        with self.assertRaises(RegistrationValidationError):
            validate_registration("Alice", "A1B2C3D4", "12A4")

    def test_normalize_nfc_uid_handles_blank_values(self):
        self.assertIsNone(normalize_nfc_uid("   "))


if __name__ == "__main__":
    unittest.main()
