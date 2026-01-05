Fix: handle token-create race during OTP verification

This small fix makes `firebase_verify` robust against a rare race where two concurrent requests attempt to create the same `FirebaseTokenUse` row simultaneously. Changes:
- Catch `IntegrityError` around `get_or_create` and fetch existing row under `select_for_update()` lock.
- Add `AuditLog` entry `firebase_token_create_race` to aid debugging.
- Add `test_token_create_race_handled` to `core/tests_security.py` to ensure the flow is correct.

This PR targets `feature/otp-concurrency-ci` as a follow-up to the concurrency test work.