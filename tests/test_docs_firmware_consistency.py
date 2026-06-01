import re
import unittest
from pathlib import Path


class TestDocsFirmwareConsistency(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    FIRMWARE_PATH = REPO_ROOT / "arduino" / "doorlock_firmware" / "doorlock_firmware.ino"
    DOC_PATHS = {
        "pin_connect_set.md": REPO_ROOT / "pin_connect_set.md",
        "HARDWARE_SPECS.md": REPO_ROOT / "HARDWARE_SPECS.md",
        "TEST_SCENARIOS.md": REPO_ROOT / "TEST_SCENARIOS.md",
    }
    WEBSITE_DOC_PATHS = {
        "architecture.md": REPO_ROOT / "website" / "docs" / "architecture.md",
        "authentication-flow.md": REPO_ROOT / "website" / "docs" / "authentication-flow.md",
        "executive-summary.md": REPO_ROOT / "website" / "docs" / "executive-summary.md",
        "intro.md": REPO_ROOT / "website" / "docs" / "intro.md",
        "problem-objective.md": REPO_ROOT / "website" / "docs" / "problem-objective.md",
    }

    REQUIRED_PINS = {"D2", "D3", "D5", "A2", "D9", "D10", "D11", "D12", "D13"}
    REQUIRED_COMMANDS = {"OPEN_DOOR", "AUTH_FAIL", "LOCKDOWN"}

    STALE_PATTERNS = {
        "unlock": re.compile(r"\bUNLOCK\b", re.IGNORECASE),
        "uno": re.compile(r"\bUNO\b", re.IGNORECASE),
        "nano": re.compile(r"\bNANO\b", re.IGNORECASE),
        "matrix": re.compile(r"4x4\s*matrix", re.IGNORECASE),
        "mock": re.compile(r"\bmock[-_\s]?arduino\b", re.IGNORECASE),
    }

    FIRMWARE_PIN_MACROS = {
        "KP_SDO_PIN": "D2",
        "KP_SCL_PIN": "D3",
        "SERVO_PIN": "D5",
        "BUZZER_IO_PIN": "A2",
        "NFC_RST_PIN": "D9",
        "NFC_SS_PIN": "D10",
    }

    # "LEGACY" lines are allowed to mention stale legacy terms when explicitly
    # marking old references.
    LEGACY_MARKERS = (
        "레거시",
        "legacy",
        "구버전",
        "구버전",
        "이전",
        "현재 사용하지 않는",
        "현재 미연결",
        "old",
    )

    def _read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_contains_token(self, text: str, token: str, path_name: str) -> None:
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])")
        if not pattern.search(text):
            self.fail(f"{path_name} missing canonical token: {token}")

    @staticmethod
    def _is_legacy_context(line: str) -> bool:
        lowered = line.lower()
        return any(marker in lowered for marker in TestDocsFirmwareConsistency.LEGACY_MARKERS)

    def _normalize_macro_pin(self, value: str) -> str:
        value = value.strip().upper()
        if value.startswith("D") or value.startswith("A"):
            return value
        return f"D{int(value)}"

    def _extract_firmware_command_tokens(self, text: str) -> set[str]:
        # Limit extraction to the command handler block so serial log format
        # strings outside command dispatch do not produce noise.
        section_match = re.search(
            r"void\s+handleServerCommand\s*\(\)\s*\{([\s\S]*?)\n\}",
            text,
            flags=re.MULTILINE,
        )
        section = section_match.group(1) if section_match else text
        return set(re.findall(r"\"([A-Z0-9_:\\-]+)\"", section))

    def test_firmware_commands_and_pins(self):
        firmware_text = self._read_text(self.FIRMWARE_PATH)

        for macro, expected_token in self.FIRMWARE_PIN_MACROS.items():
            match = re.search(
                rf"^\s*#define\s+{re.escape(macro)}\s+([^\s/]+)",
                firmware_text,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(
                match,
                f"Missing macro definition: {macro}",
            )
            normalized = self._normalize_macro_pin(match.group(1))
            self.assertEqual(
                normalized,
                expected_token,
                f"{macro} expected {expected_token} but parsed {normalized}",
            )

        firmware_tokens = self._extract_firmware_command_tokens(firmware_text)
        for command in self.REQUIRED_COMMANDS:
            self.assertIn(
                command,
                firmware_tokens,
                f"Firmware should define command {command} in handleServerCommand()",
            )

        # NFC path in the current firmware relies on SPI, so SPI headers must be
        # present and visible.
        self.assertIn("#include <SPI.h>", firmware_text)
        self.assertIn("MFRC522 mfrc522", firmware_text)

        # Open-command alias is intentionally retained; check that it is still the
        # documented path rather than legacy UNLOCK usage.
        self.assertIn("ACTION:OPEN", firmware_text)
        self.assertNotIn("UNLOCK", firmware_tokens)

    def test_required_pins_documented(self):
        pin_docs_text = {
            name: self._read_text(path)
            for name, path in self.DOC_PATHS.items()
        }

        # Hardware-oriented docs should explicitly list all canonical pin labels.
        for doc_name, text in pin_docs_text.items():
            if doc_name == "TEST_SCENARIOS.md":
                continue
            for token in sorted(self.REQUIRED_PINS):
                self._assert_contains_token(text.upper(), token, f"{doc_name}")

        # WEBSITE docs include architecture references and should contain the open
        # command token at least once.
        website_text = "\n".join(self._read_text(path) for path in self.WEBSITE_DOC_PATHS.values())
        self._assert_contains_token(website_text.upper(), "OPEN_DOOR", "website docs")

    def test_required_commands_documented(self):
        docs_text = {name: self._read_text(path) for name, path in self.DOC_PATHS.items()}

        for doc_name, text in docs_text.items():
            for command in self.REQUIRED_COMMANDS:
                self._assert_contains_token(text.upper(), command, doc_name)

    def test_no_stale_terms_without_legacy_caveat(self):
        all_docs = {**self.DOC_PATHS, **self.WEBSITE_DOC_PATHS}
        for doc_name, path in all_docs.items():
            text = self._read_text(path)
            for line_no, line in enumerate(text.splitlines(), start=1):
                line_lower = line.lower()
                if "레거시" in line_lower or "legacy" in line_lower:
                    continue
                if self._is_legacy_context(line):
                    continue

                # "UNO R4" is canonical and should not be treated as stale.
                if "r4" in line_lower and "uno" in line_lower:
                    continue

                for stale_name, pattern in self.STALE_PATTERNS.items():
                    if pattern.search(line):
                        self.fail(
                            f"Stale term '{stale_name}' found in {doc_name} "
                            f"line {line_no}: {line.strip()}"
                        )
