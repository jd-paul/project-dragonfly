from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from with_asserts.mixin import AssertHTMLMixin
from tutorials.helpers import login_prohibited
from tutorials.models import User, UserType

def reverse_with_next(url_name, next_url):
    """Extended version of reverse to generate URLs with redirects."""
    url = reverse(url_name)
    url += f"?next={next_url}"
    return url

class LogInTester:
    """Class to support login tests."""

    def _is_logged_in(self):
        """Returns True if a user is logged in, False otherwise."""
        return '_auth_user_id' in self.client.session.keys()

class MenuTesterMixin(AssertHTMLMixin):
    """Class to extend tests with tools to check the presence of menu items."""

    menu_urls = [
        reverse('password'), reverse('profile'), reverse('log_out')
    ]

    def assert_menu(self, response):
        """Check that menu is present in the response."""
        for url in self.menu_urls:
            with self.assertHTML(response, f'a[href="{url}"]'):
                pass

    def assert_no_menu(self, response):
        """Check that no menu is present in the response."""
        for url in self.menu_urls:
            self.assertNotHTML(response, f'a[href="{url}"]')

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
        response = self.client.get(reverse('some_authenticated_view'))  # Replace with a real view name
        self.assert_menu(response)

    def test_menu_not_present_for_anonymous_user(self):
        """Test that the menu is not present for an anonymous user."""
        response = self.client.get(reverse('home'))  # Replace with your public view
        self.assert_no_menu(response)
