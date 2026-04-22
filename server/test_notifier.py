import unittest
from unittest.mock import Mock, patch

from notifier import Notifier


class TestNotifier(unittest.TestCase):
    @patch("notifier.requests.post")
    def test_webhook_request_uses_timeout(self, mock_post):
        mock_post.return_value = Mock(status_code=204)
        notifier = Notifier("https://example.test/webhook", timeout_seconds=1.25)

        notifier.send_security_alert("test message")

        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs["timeout"], 1.25)
        self.assertEqual(mock_post.call_args.kwargs["json"]["allowed_mentions"], {"parse": []})

    @patch("notifier.requests.post")
    def test_webhook_with_snapshot_uses_payload_json(self, mock_post):
        mock_post.return_value = Mock(status_code=204)
        notifier = Notifier("https://example.test/webhook", timeout_seconds=1.25)

        notifier.send_security_alert("@everyone", snapshot_bytes=b"jpeg")

        mock_post.assert_called_once()
        payload_json = mock_post.call_args.kwargs["data"]["payload_json"]
        self.assertIn('"allowed_mentions": {"parse": []}', payload_json)
        self.assertIn('"content"', payload_json)

    @patch("notifier.requests.post")
    def test_missing_webhook_skips_network(self, mock_post):
        notifier = Notifier("")

        notifier.send_security_alert("test message")

        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
