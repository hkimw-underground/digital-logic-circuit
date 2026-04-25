## 2024-05-17 - Insecure Deserialization in Face Encoding
**Vulnerability:** The legacy face encoding logic in `vision_ai.py` used `pickle.loads()` which could be bypassed to cause arbitrary code execution (Insecure Deserialization) by uploading a malicious payload as a face encoding.
**Learning:** Even though the codebase contained a flag `ALLOW_LEGACY_FACE_PICKLE` intended to be disabled, the presence of `pickle.loads()` itself poses a risk if an attacker can manipulate environment variables, or if the config defaults were poorly handled. Python's `pickle` module must never be used with untrusted data.
**Prevention:** Completely remove the `pickle` module from imports. Only use secure serialization formats like NumPy byte sequences or JSON.
