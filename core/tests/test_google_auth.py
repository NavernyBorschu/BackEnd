"""Тести Google OAuth + JWT (mock верифікації токена)."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import UserProfile


def _google_claims(**overrides):
    base = {
        'iss': 'https://accounts.google.com',
        'sub': 'google-sub-123',
        'email': 'oauth@example.com',
        'email_verified': True,
        'given_name': 'OAuth',
        'family_name': 'User',
        'locale': 'uk',
        'picture': 'https://lh3.googleusercontent.com/a/abc',
        'aud': 'test-google-client-id.apps.googleusercontent.com',
    }
    base.update(overrides)
    return base


class GoogleAuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('core.oauth_google.id_token.verify_oauth2_token')
    def test_google_auth_creates_user_and_profile(self, mock_verify):
        mock_verify.return_value = _google_claims()

        response = self.client.post(
            '/api/auth/google/',
            {'id_token': 'dummy.jwt.token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('profile', response.data)

        user = User.objects.get(email='oauth@example.com')
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.google_id, 'google-sub-123')
        self.assertEqual(profile.given_name, 'OAuth')

    @patch('core.oauth_google.id_token.verify_oauth2_token')
    def test_google_auth_conflict_when_email_linked_to_other_google(self, mock_verify):
        user = User.objects.create_user(
            username='existing',
            email='same@example.com',
            password='x',
        )
        UserProfile.objects.create(
            user=user,
            google_id='another-google-sub',
            given_name='Old',
        )

        mock_verify.return_value = _google_claims(
            sub='new-google-sub',
            email='same@example.com',
        )

        response = self.client.post(
            '/api/auth/google/',
            {'id_token': 'dummy'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
