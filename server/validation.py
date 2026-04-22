import re


NFC_UID_RE = re.compile(r"^[0-9A-F]{4,32}$")


class RegistrationValidationError(ValueError):
    pass


def normalize_nfc_uid(nfc_uid):
    if nfc_uid is None:
        return None
    value = str(nfc_uid).strip().upper()
    return value or None


def validate_registration(name, nfc_uid, password):
    username = "" if name is None else str(name).strip()
    normalized_uid = normalize_nfc_uid(nfc_uid)
    pin = "" if password is None else str(password).strip()

    if not username:
        raise RegistrationValidationError("Name is required.")
    if len(username) > 80:
        raise RegistrationValidationError("Name must be 80 characters or fewer.")
    if any(ord(char) < 32 for char in username):
        raise RegistrationValidationError("Name cannot contain control characters.")
    if not normalized_uid or not NFC_UID_RE.fullmatch(normalized_uid):
        raise RegistrationValidationError("NFC UID must be 4 to 32 hexadecimal characters.")
    if not pin.isdigit() or not 4 <= len(pin) <= 8:
        raise RegistrationValidationError("PIN must be 4 to 8 digits.")

    return username, normalized_uid, pin
