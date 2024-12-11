from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tutorials.models import User, UserType, StudentRequest, Skill


class ManageApplicationsTests(TestCase):
    """Test the ManageApplications view."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Use existing users from the fixture
        self.admin_user = User.objects.get(username='@adminuser')  # Admin user
        self.student1 = User.objects.get(username='@studentuser')  # Student user
        self.tutor = User.objects.get(username='@tutoruser')  # Tutor user (not directly used here)

        # Skill
        self.skill = Skill.objects.create(
            language="Python",
            level="Beginner",
        )

        # Valid student requests
        self.request1 = StudentRequest.objects.create(
            student=self.student1,
            skill=self.skill,
            duration=60,
            status="pending",
            created_at=timezone.now(),
        )
        self.request2 = StudentRequest.objects.create(
            student=self.student1,
            skill=self.skill,
            duration=30,
            status="approved",
            created_at=timezone.now(),
        )

        # URL for the ManageApplications view
        self.url = reverse('manage_applications')

    def test_admin_can_access_manage_applications(self):
        """Test that an admin user can access the ManageApplications view."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_applications.html')

    def test_non_admin_cannot_access_manage_applications(self):
        """Test that a non-admin user cannot access the ManageApplications view."""
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_anonymous_user_redirected(self):
        """Test that an anonymous user is redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith(reverse('log_in')))
