import os
import unittest
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from apps.users.authentication import FirebaseAuthentication


class FirebaseAuthenticationTestCase(TestCase):
    def setUp(self):
        self.auth = FirebaseAuthentication()
        self.User = get_user_model()

    @patch('firebase_admin.auth.verify_id_token')
    def test_valid_token_resolves_user(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'firebase_uid_123',
            'phone_number': '+919876543210'
        }
        user = self.User.objects.create_user(
            phone_number='+919876543210',
            firebase_uid='firebase_uid_123',
            role='CUSTOMER'
        )

        class MockRequest:
            META = {'HTTP_AUTHORIZATION': 'Bearer valid_token_abc'}

        request = MockRequest()
        authenticated_user, claims = self.auth.authenticate(request)

        self.assertEqual(authenticated_user, user)
        self.assertEqual(claims['uid'], 'firebase_uid_123')

    @patch('firebase_admin.auth.verify_id_token')
    def test_invalid_expired_token_rejected(self, mock_verify):
        mock_verify.side_effect = Exception('Token expired or invalid signature')

        class MockRequest:
            META = {'HTTP_AUTHORIZATION': 'Bearer invalid_token_xyz'}

        request = MockRequest()
        with self.assertRaises(AuthenticationFailed) as excinfo:
            self.auth.authenticate(request)
        self.assertIn('token', str(excinfo.exception).lower())

    @patch('firebase_admin.auth.verify_id_token')
    def test_unknown_uid_rejection(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'unknown_uid_999'
        }

        class MockRequest:
            META = {'HTTP_AUTHORIZATION': 'Bearer unknown_token'}

        request = MockRequest()
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch('firebase_admin.auth.verify_id_token')
    def test_inactive_account_rejection(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'inactive_uid_456',
            'phone_number': '+919876543212'
        }
        self.User.objects.create_user(
            phone_number='+919876543212',
            firebase_uid='inactive_uid_456',
            is_active=False
        )

        class MockRequest:
            META = {'HTTP_AUTHORIZATION': 'Bearer inactive_token'}

        request = MockRequest()
        with self.assertRaises(AuthenticationFailed) as excinfo:
            self.auth.authenticate(request)
        self.assertIn('inactive', str(excinfo.exception).lower())

    @patch('firebase_admin.auth.verify_id_token')
    def test_no_client_controlled_role_escalation(self, mock_verify):
        mock_verify.return_value = {
            'uid': 'customer_uid_789',
            'phone_number': '+919876543213',
            'role': 'ADMIN'
        }
        user = self.User.objects.create_user(
            phone_number='+919876543213',
            firebase_uid='customer_uid_789',
            role='CUSTOMER'
        )

        class MockRequest:
            META = {'HTTP_AUTHORIZATION': 'Bearer token_customer'}

        request = MockRequest()
        authenticated_user, _ = self.auth.authenticate(request)
        self.assertEqual(authenticated_user.role, 'CUSTOMER')


if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    django.setup()
    unittest.main()
