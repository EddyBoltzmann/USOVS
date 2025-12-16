from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Election, Candidate, Vote
from django.utils import timezone
import datetime

class FirebaseVerifyTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_verify_missing_token(self):
        resp = self.client.post(reverse('firebase_verify'), content_type='application/json', data={})
        self.assertEqual(resp.status_code, 400)


class VotingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='u1', password='pass')
        self.election = Election.objects.create(title='E', start_time=timezone.now() - datetime.timedelta(hours=1), end_time=timezone.now() + datetime.timedelta(hours=1))
        self.candidate = Candidate.objects.create(election=self.election, name='C1')

    def test_cast_vote(self):
        self.client.login(username='u1', password='pass')
        resp = self.client.post(reverse('cast_vote', args=[self.election.id]), {'candidate_id': self.candidate.id})
        self.assertContains(resp, 'Thanks for voting')
        self.assertEqual(Vote.objects.count(), 1)

    def test_vote_outside_window(self):
        self.election.start_time = timezone.now() + datetime.timedelta(days=1)
        self.election.save()
        self.client.login(username='u1', password='pass')
        resp = self.client.post(reverse('cast_vote', args=[self.election.id]), {'candidate_id': self.candidate.id})
        self.assertContains(resp, 'Voting closed')

    def test_admin_export_csv_admin_access(self):
        admin = User.objects.create_user(username='admin', password='pass', is_election_admin=True)
        Vote.objects.create(election=self.election, voter=self.user, candidate=self.candidate)
        self.client.force_login(admin, backend='django.contrib.auth.backends.ModelBackend')
        resp = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        self.assertIn(self.candidate.name, resp.content.decode())

    def test_admin_export_csv_non_admin_forbidden(self):
        normal = User.objects.create_user(username='normal', password='pass')
        self.client.force_login(normal, backend='django.contrib.auth.backends.ModelBackend')
        resp = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(resp.status_code, 403)

    def test_admin_export_csv_unauth_redirect(self):
        resp = self.client.get(reverse('admin_export_csv', args=[self.election.id]))
        self.assertEqual(resp.status_code, 302)

    def test_double_vote(self):
        self.client.login(username='u1', password='pass')
        self.client.post(reverse('cast_vote', args=[self.election.id]), {'candidate_id': self.candidate.id})
        resp = self.client.post(reverse('cast_vote', args=[self.election.id]), {'candidate_id': self.candidate.id})
        self.assertContains(resp, 'already voted')
        self.assertEqual(Vote.objects.count(), 1)
