from django.test import LiveServerTestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib

try:
    import requests
except Exception:
    requests = None

class OTPConcurrencyTests(LiveServerTestCase):
    @override_settings(FIREBASE_VERIFICATION_MAX_ATTEMPTS_PER_IP=1000)
    def test_concurrent_verifications_only_one_succeeds(self):
        if requests is None:
            self.skipTest('requests library not available')

        # Skip concurrency DB test on SQLite since SQLite does not support the required
        # concurrent transaction semantics (savepoints/SELECT FOR UPDATE), and in-memory
        # SQLite may produce spurious 'no such savepoint' / transaction errors.
        from django.db import connection
        if connection.vendor == 'sqlite':
            self.skipTest('Database backend is SQLite; run concurrency tests with Postgres or MySQL')

        decoded = {'uid': 'concurrent-uid', 'email': 'concurrent@uni.edu', 'iat': int(timezone.now().timestamp())}

        with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
            url = self.live_server_url + reverse('firebase_verify')
            payload = {'id_token': 'same-token'}

            def do_request():
                r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                return r.status_code, r.text

            # Fire several concurrent requests for the same token
            with ThreadPoolExecutor(max_workers=8) as ex:
                results = list(ex.map(lambda _: do_request(), range(8)))

            statuses = [r[0] for r in results]
            # Expect exactly one success (200) and the rest token_reuse (403)
            self.assertEqual(statuses.count(200), 1)
            self.assertGreaterEqual(statuses.count(403), 7)
