from django.test import TestCase
from django.core.exceptions import PermissionDenied
from tutorials.models import User
from tutorials.views import is_admin, is_student, is_tutor
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from tutorials.tests.helpers import MenuTesterMixin
from tutorials.helpers import login_prohibited
from tutorials.models import User

class HelperFunctionsTestCase(TestCase):
    """Test is_admin, is_student, and is_tutor helper functions."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        self.admin = User.objects.get(username='@adminuser')
        self.student = User.objects.get(username='@studentuser')
        self.tutor = User.objects.get(username='@tutoruser')

    def test_is_admin_with_admin_user(self):
        self.assertTrue(is_admin(self.admin))

    def test_is_admin_with_non_admin_raises(self):
        with self.assertRaises(PermissionDenied):
            is_admin(self.student)
        with self.assertRaises(PermissionDenied):
            is_admin(self.tutor)

    def test_is_student_with_student_user(self):
        self.assertTrue(is_student(self.student))

    def test_is_student_with_non_student_raises(self):
        with self.assertRaises(PermissionDenied):
            is_student(self.admin)
        with self.assertRaises(PermissionDenied):
            is_student(self.tutor)

    def test_is_tutor_with_tutor_user(self):
        self.assertTrue(is_tutor(self.tutor))

    def test_is_tutor_with_non_tutor_raises(self):
        with self.assertRaises(PermissionDenied):
            is_tutor(self.admin)
        with self.assertRaises(PermissionDenied):
            is_tutor(self.student)

class LoginProhibitedDecoratorTestCase(TestCase, MenuTesterMixin):
    """Test the `login_prohibited` decorator and related functionality."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Load users from fixture
        self.student = User.objects.get(username='@studentuser')  # Student user
        self.admin = User.objects.get(username='@adminuser')  # Admin user

        # RequestFactory for simulating requests
        self.factory = RequestFactory()

    def test_login_prohibited_redirects_logged_in_user(self):
        """Test that a logged-in user is redirected by the decorator."""

        # Simulate a logged-in user
        request = self.factory.get('/test-url/')
        request.user = self.student

        # Define a test view
        @login_prohibited
        def test_view(request):
            return HttpResponse("This is a test view")

        # Call the view with a logged-in user
        response = test_view(request)

        # Normalize the expected URL for comparison
        expected_url = f"/{settings.REDIRECT_URL_WHEN_LOGGED_IN}".rstrip("/") + "/"

        # Assert the response is a redirect (HTTP 302)
        self.assertEqual(response.status_code, 302, "Expected a 302 redirect status code.")

        # Assert the redirect URL matches the expected URL
        self.assertEqual(response.url, expected_url, f"Expected redirect to '{expected_url}' but got '{response.url}'.")

    def test_login_prohibited_allows_anonymous_user(self):
        """Test that an anonymous user is allowed to access the view."""

        # Simulate an anonymous user
        request = self.factory.get('/test-url/')
        request.user = AnonymousUser()

        # Define a test view
        @login_prohibited
        def test_view(request):
            return HttpResponse("This is a test view")

        # Call the view with an anonymous user
        response = test_view(request)

        # Assert the original view response is as expected
        self.assertEqual(response.status_code, 200, "Expected a 200 OK status code for anonymous user.")
        self.assertEqual(response.content, b"This is a test view", "Unexpected response content for anonymous user.")

    def test_menu_present_for_logged_in_user(self):
        """Test that the menu is present for a logged-in user."""
        self.client.login(username='@studentuser', password='password123')
        response = self.client.get(reverse('dashboard'))  # Replace with a real view name
        self.assert_menu(response)

    def test_menu_not_present_for_anonymous_user(self):
        """Test that the menu is not present for an anonymous user."""
        response = self.client.get(reverse('home'))  # Replace with your public view
        self.assert_no_menu(response)
