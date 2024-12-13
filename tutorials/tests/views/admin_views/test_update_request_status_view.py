from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from tutorials.models import User, UserType, Skill, StudentRequest
from django.utils import timezone


class UpdateRequestStatusViewTests(TestCase):
    """Tests for the update_request_status view."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Use existing users from the fixture
        self.admin_user = User.objects.get(username='@adminuser')  # Admin user
        self.student = User.objects.get(username='@studentuser')  # Student user

        # Create a skill
        self.skill = Skill.objects.create(language="Python", level="Beginner")

        # Create a student request
        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=60,
            status="pending",
            created_at=timezone.now(),
        )

        # URLs for update_request_status actions
        self.approve_url = reverse('update_request_status', args=[self.student_request.id, 'approve'])
        self.reject_url = reverse('update_request_status', args=[self.student_request.id, 'reject'])
        self.pending_url = reverse('update_request_status', args=[self.student_request.id, 'pending'])
        self.invalid_url = reverse('update_request_status', args=[self.student_request.id, 'invalid'])

    def login_as_admin(self):
        """Helper method to log in as admin user."""
        self.client.login(username='@adminuser', password='Password123')

    def test_approve_request_redirects_to_manage_applications(self):
        """Test approving a request redirects to manage_applications."""
        self.login_as_admin()
        response = self.client.get(self.approve_url)
        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.status, 'approved')
        self.assertRedirects(response, reverse('manage_applications'))
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn(f"Request {self.student_request.id} has been approved.", messages)

    def test_reject_request_refreshes_page(self):
        """Test rejecting a request refreshes the current page."""
        self.login_as_admin()
        referer_url = '/manage_applications/'
        response = self.client.get(self.reject_url, HTTP_REFERER=referer_url)

        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.status, 'rejected')
        self.assertRedirects(response, referer_url)
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn(f"Request {self.student_request.id} has been rejected.", messages)

    def test_set_request_to_pending_refreshes_page(self):
        """Test setting a request to pending refreshes the current page."""
        self.login_as_admin()
        referer_url = '/manage_applications/'
        response = self.client.get(self.pending_url, HTTP_REFERER=referer_url)

        self.student_request.refresh_from_db()
        self.assertEqual(self.student_request.status, 'pending')
        self.assertRedirects(response, referer_url)
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn(f"Request {self.student_request.id} has been set to pending.", messages)

    def test_invalid_action_redirects_to_manage_applications(self):
        """Test that an invalid action redirects to manage_applications with an error message."""
        self.login_as_admin()
        response = self.client.get(self.invalid_url)

        self.assertRedirects(response, reverse('manage_applications'))
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn("Invalid action.", messages)

    def test_non_admin_cannot_update_request(self):
        """Test that a non-admin user cannot update a request."""
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(self.approve_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
