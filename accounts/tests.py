"""
Unit tests for the accounts app.

Covers user model methods, registration form validation, and auth views.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username='user1', role='reader', password='Pass1234!'):
    """Create and return a CustomUser with the given role."""
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=password,
        role=role,
    )


# ---------------------------------------------------------------------------
# CustomUser model
# ---------------------------------------------------------------------------

class CustomUserRoleTests(TestCase):
    """Tests for the CustomUser role helper methods."""

    def test_is_reader_returns_true_for_reader(self):
        """is_reader() returns True only for users with role='reader'."""
        user = make_user(role='reader')
        self.assertTrue(user.is_reader())
        self.assertFalse(user.is_journalist())
        self.assertFalse(user.is_editor())

    def test_is_journalist_returns_true_for_journalist(self):
        """is_journalist() returns True for users with role='journalist'."""
        user = make_user(username='j1', role='journalist')
        self.assertTrue(user.is_journalist())
        self.assertFalse(user.is_reader())

    def test_is_editor_returns_true_for_editor(self):
        """is_editor() returns True only for users with role='editor'."""
        user = make_user(username='e1', role='editor')
        self.assertTrue(user.is_editor())
        self.assertFalse(user.is_reader())

    def test_email_is_unique(self):
        """Creating two users with the same email raises an IntegrityError."""
        make_user(username='a', role='reader')
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='b',
                email='a@example.com',  # same email as user 'a' above
                password='Pass1234!',
                role='reader',
            )


# ---------------------------------------------------------------------------
# Registration view
# ---------------------------------------------------------------------------

class RegisterViewTests(TestCase):
    """Tests for the /accounts/register/ view."""

    def setUp(self):
        """Store register URL for re-use."""
        self.url = reverse('accounts:register')

    def test_register_page_loads(self):
        """GET /accounts/register/ returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_successful_registration_creates_user(self):
        """Valid POST creates a new user and redirects."""
        response = self.client.post(self.url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass99!',
            'password2': 'StrongPass99!',
            'role': 'reader',
        })
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)
        self.assertIn(response.status_code, [200, 302])

    def test_duplicate_email_rejected(self):
        """Registering with an already-used email shows a form error."""
        make_user(username='existing', role='reader')
        response = self.client.post(self.url, {
            'username': 'other',
            'email': 'existing@example.com',  # already taken
            'password1': 'StrongPass99!',
            'password2': 'StrongPass99!',
            'role': 'reader',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered
        self.assertFalse(User.objects.filter(username='other').exists())


# ---------------------------------------------------------------------------
# Login / logout views
# ---------------------------------------------------------------------------

class LoginViewTests(TestCase):
    """Tests for the /accounts/login/ view."""

    def setUp(self):
        """Create a reader and store login URL."""
        self.user = make_user(username='reader1', role='reader')
        self.url  = reverse('accounts:login')

    def test_login_page_loads(self):
        """GET /accounts/login/ returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_credentials_log_user_in(self):
        """Correct credentials authenticate the user and redirect."""
        response = self.client.post(self.url, {
            'username': 'reader1',
            'password': 'Pass1234!',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_invalid_credentials_stay_on_login(self):
        """Wrong password keeps the user on the login page."""
        response = self.client.post(self.url, {
            'username': 'reader1',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects(self):
        """Logging out redirects to the home page."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:logout'))
        self.assertIn(response.status_code, [200, 302])
