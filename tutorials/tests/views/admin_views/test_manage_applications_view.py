from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tutorials.models import User, UserType, StudentRequest, Skill
from datetime import timedelta


class ManageApplicationsTests(TestCase):
    """Test the ManageApplications view."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Use existing users from the fixture
        self.admin_user = User.objects.get(username='@adminuser')  # Admin user
        self.student1 = User.objects.get(username='@studentuser')  # Student user
        self.tutor = User.objects.get(username='@tutoruser')      # Tutor user (not directly used here)

        # Update student1's name for clarity
        self.student1.first_name = 'John'
        self.student1.last_name = 'Doe'
        self.student1.save()

        # Create another student for sorting by student name
        self.student2 = User.objects.create_user(
            username='@student2',
            password='Password123',
            user_type=UserType.STUDENT,
            first_name='Alice',
            last_name='Smith',
            email='alice.smith@example.com',
            # Add other necessary fields as required by your User model
        )

        # Skill
        self.skill = Skill.objects.create(
            language="Python",
            level="Beginner",
        )

        # Valid student requests with distinct created_at
        self.request1 = StudentRequest.objects.create(
            student=self.student1,
            skill=self.skill,
            duration=60,
            status="pending",
            created_at=timezone.now(),
        )
        self.request2 = StudentRequest.objects.create(
            student=self.student2,
            skill=self.skill,
            duration=30,
            status="approved",
            created_at=timezone.now() + timedelta(seconds=1),  # Ensure request2 is created after request1
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

    def test_sort_by_student_asc(self):
        """Test sorting requests by student name in ascending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'student', 'order': 'asc'})
        self.assertEqual(response.status_code, 200)
        # Since Alice Smith comes before John Doe alphabetically
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request2, self.request1]
        )

    def test_sort_by_student_desc(self):
        """Test sorting requests by student name in descending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'student', 'order': 'desc'})
        self.assertEqual(response.status_code, 200)
        # In descending order, John Doe comes before Alice Smith
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request1, self.request2]
        )

    def test_sort_by_duration_asc(self):
        """Test sorting requests by duration in ascending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'duration', 'order': 'asc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request2, self.request1]
        )

    def test_sort_by_duration_desc(self):
        """Test sorting requests by duration in descending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'duration', 'order': 'desc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request1, self.request2]
        )

    def test_sort_by_status_pending(self):
        """Test sorting requests by status (pending first)."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'status', 'order': 'asc_pending'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request1, self.request2]
        )

    def test_sort_by_status_approved(self):
        """Test sorting requests by status (approved first)."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'status', 'order': 'asc_approved'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request2, self.request1]
        )

    def test_sort_by_status_rejected(self):
        """Test sorting requests by status (rejected first)."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'status', 'order': 'asc_rejected'})
        self.assertEqual(response.status_code, 200)
        # No rejected requests in this setup, so order remains unchanged
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request1, self.request2]
        )

    def test_sort_by_created_at_asc(self):
        """Test sorting requests by creation date in ascending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'created_at', 'order': 'asc'})
        self.assertEqual(response.status_code, 200)
        # request1 was created before request2
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request1, self.request2]
        )

    def test_sort_by_created_at_desc(self):
        """Test sorting requests by creation date in descending order."""
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url, {'sort_by': 'created_at', 'order': 'desc'})
        self.assertEqual(response.status_code, 200)
        # request2 was created after request1
        self.assertEqual(
            list(response.context['student_requests']),
            [self.request2, self.request1]
        )
