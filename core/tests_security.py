from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Election, Candidate, Vote, AuditLog
from django.utils import timezone
import datetime
from django.db import IntegrityError
from unittest.mock import patch


class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u1', password='pass')
        self.election = Election.objects.create(title='SecE', start_time=timezone.now() - datetime.timedelta(hours=2), end_time=timezone.now() + datetime.timedelta(hours=2))
        self.candidate = Candidate.objects.create(election=self.election, name='C1')

    def test_double_vote_db_constraint(self):
        # ensure DB constraint enforces uniqueness
        Vote.objects.create(election=self.election, voter=self.user, candidate=self.candidate)
        with self.assertRaises(IntegrityError):
            Vote.objects.create(election=self.election, voter=self.user, candidate=self.candidate)

    def test_otp_replay_is_blocked_and_logged(self):
        # Mock firebase token verification to return a stable uid
        decoded = {'uid': 'firebase-uid-123', 'email': 'student@uni.edu', 'phone_number': None, 'iat': int(timezone.now().timestamp())}

        with patch('firebase_admin.auth.verify_id_token', return_value=decoded) as mock_verify:
            resp1 = self.client.post(reverse('firebase_verify'), data='{"id_token": "tok"}', content_type='application/json')
            self.assertEqual(resp1.status_code, 200)
            resp2 = self.client.post(reverse('firebase_verify'), data='{"id_token": "tok"}', content_type='application/json')
            # Replay must be rejected
            self.assertEqual(resp2.status_code, 403)

        users = User.objects.filter(firebase_uid='firebase-uid-123')
        self.assertEqual(users.count(), 1, 'OTP replay should not create duplicate users')

        # Audit logs should record the token reuse attempt
        reuse_logs = AuditLog.objects.filter(action='firebase_token_reuse', details__uid='firebase-uid-123')
        self.assertGreaterEqual(reuse_logs.count(), 1)

    def test_token_create_race_handled(self):
        # Simulate a concurrent create race by pre-creating the token before verification
        decoded = {'uid': 'race-uid', 'email': 'race@uni.edu', 'iat': int(timezone.now().timestamp())}
        import hashlib
        token_hash = hashlib.sha256('tokrace'.encode()).hexdigest()
        from .firebase_models import FirebaseTokenUse
        FirebaseTokenUse.objects.create(token_hash=token_hash, uid=decoded['uid'], issued_at=timezone.now())

        with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
            resp = self.client.post(reverse('firebase_verify'), data='{"id_token": "tokrace"}', content_type='application/json')
            self.assertEqual(resp.status_code, 200)
            resp2 = self.client.post(reverse('firebase_verify'), data='{"id_token": "tokrace"}', content_type='application/json')
            self.assertEqual(resp2.status_code, 403)

    def test_per_ip_attempt_limit_triggers(self):
        # Force a low limit for test
        from django.test import override_settings
        with override_settings(FIREBASE_VERIFICATION_MAX_ATTEMPTS_PER_IP=2, FIREBASE_VERIFICATION_WINDOW_SECONDS=3600):
            with patch('firebase_admin.auth.verify_id_token', side_effect=Exception('invalid')):
                resp1 = self.client.post(reverse('firebase_verify'), data='{"id_token": "bad1"}', content_type='application/json')
                self.assertEqual(resp1.status_code, 400)
                resp2 = self.client.post(reverse('firebase_verify'), data='{"id_token": "bad2"}', content_type='application/json')
                self.assertEqual(resp2.status_code, 400)
                resp3 = self.client.post(reverse('firebase_verify'), data='{"id_token": "bad3"}', content_type='application/json')
                # Now rate-limited
                self.assertEqual(resp3.status_code, 429)

    def test_token_age_rejection(self):
        old_iat = int((timezone.now() - datetime.timedelta(hours=2)).timestamp())
        decoded = {'uid': 'firebase-uid-456', 'email': 'student@uni.edu', 'phone_number': None, 'iat': old_iat}
        with patch('firebase_admin.auth.verify_id_token', return_value=decoded):
            resp = self.client.post(reverse('firebase_verify'), data='{"id_token": "tok2"}', content_type='application/json')
            self.assertEqual(resp.status_code, 400)
            self.assertIn('token_too_old', resp.content.decode())

    def test_log_otp_sent_endpoint(self):
        resp = self.client.post(reverse('log_otp_sent'), data='{"method":"sms","address":"+123"}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        from .firebase_models import OTPSendLog
        self.assertEqual(OTPSendLog.objects.count(), 1)

    def test_voting_after_election_close(self):
        # election closed in the past
        self.election.start_time = timezone.now() - datetime.timedelta(days=2)
        self.election.end_time = timezone.now() - datetime.timedelta(days=1)
        self.election.save()

        self.client.login(username='u1', password='pass')
        resp = self.client.post(reverse('cast_vote', args=[self.election.id]), {'candidate_id': self.candidate.id})
        self.assertContains(resp, 'Voting closed')

    def test_unauthorized_result_export_attempts(self):
        Vote.objects.create(election=self.election, voter=self.user, candidate=self.candidate)
        # non-admin user
        normal = User.objects.create_user(username='normal', password='pass')
        self.client.force_login(normal)
        resp = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(resp.status_code, 403)

        # unauthenticated
        self.client.logout()
        unauth = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(unauth.status_code, 302)

        # admin access works
        admin = User.objects.create_user(username='admin', password='pass', is_election_admin=True)
        self.client.force_login(admin)
        resp = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.candidate.name, resp.content.decode())
