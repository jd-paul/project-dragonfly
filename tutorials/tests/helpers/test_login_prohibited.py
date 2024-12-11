from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings  # Ensure settings is imported
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from tutorials.helpers import login_prohibited
from tutorials.models import User, UserType


class LoginProhibitedDecoratorTestCase(TestCase):
    """Test the `login_prohibited` decorator."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Load users from fixture
        self.student = User.objects.get(username='@studentuser')  # Student user
        self.admin = User.objects.get(username='@adminuser')  # Admin user (not directly used here)

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
        # Ensure the expected URL starts with a leading slash
        expected_url = '/' + settings.REDIRECT_URL_WHEN_LOGGED_IN.strip('/') + '/'

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
