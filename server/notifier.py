import json
import requests
import io

from config import NOTIFIER_TIMEOUT_SECONDS

class Notifier:
    def __init__(self, webhook_url=None, timeout_seconds=NOTIFIER_TIMEOUT_SECONDS):
        # 사용자가 설정한 Discord Webhook URL (없으면 알림 건너뜀)
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_security_alert(self, message, snapshot_bytes=None):
        if not self.webhook_url:
            print(f"[NOTIFIER] No Webhook URL set. Alert: {message}")
            return
            
        payload = {
            "content": f"Doorlock alert\n{message}",
            "allowed_mentions": {"parse": []},
        }
        
        try:
            if snapshot_bytes:
                files = {"file": ("intruder.jpg", io.BytesIO(snapshot_bytes), "image/jpeg")}
                response = requests.post(
                    self.webhook_url,
                    data={"payload_json": json.dumps(payload)},
                    files=files,
                    timeout=self.timeout_seconds,
                )
            else:
                response = requests.post(self.webhook_url, json=payload, timeout=self.timeout_seconds)
                
            if response.status_code == 204 or response.status_code == 200:
                print("[NOTIFIER] Security alert sent to Discord.")
            else:
                print(f"[NOTIFIER] Failed to send alert: {response.status_code}")
        except Exception as e:
            print(f"[NOTIFIER] Error sending notification: {e}")
