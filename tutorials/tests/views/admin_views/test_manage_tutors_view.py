from django.test import TestCase
from django.urls import reverse
from tutorials.models import User, PendingTutor, TutorSkill, Skill, UserType

class ManageTutorsViewTestCase(TestCase):
    """Test the ManageTutors view."""
    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Admin user
        self.admin = User.objects.get(username='@adminuser')

        # Tutor user
        self.tutor = User.objects.get(username='@tutoruser')

        # Skill for the tutor
        self.skill = Skill.objects.create(
            language="Python",
            level="Beginner",
        )

        # TutorSkill for the approved tutors list
        self.tutor_skill = TutorSkill.objects.create(
            tutor=self.tutor,
            skill=self.skill,
            price_per_hour=50,
        )

        # PendingTutor for the pending tutors list
        self.pending_tutor = PendingTutor.objects.create(
            user=self.tutor,
            is_approved=False,
            price_per_hour=40,
        )

        # URL for the ManageTutors view
        self.url = reverse('manage_tutors')

    def test_manage_tutors_get_by_admin(self):
        """Test that an admin user can access the ManageTutors view."""
        # Log in as admin
        self.client.login(username='@adminuser', password='Password123')

        # Access the ManageTutors view
        response = self.client.get(self.url)

        # Assert correct status code and template usage
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tutors.html')

        # Assert pending tutors in the context
        tutors = response.context['tutors'].object_list  # Pending tutors (paginated)
        self.assertIn(self.pending_tutor, tutors)

        # Assert approved tutors in the context
        current_tutors = response.context['current_tutors']
        self.assertIn(self.tutor, current_tutors)

    def test_manage_tutors_get_by_non_admin(self):
        """Test that a non-admin user cannot access the ManageTutors view."""
        # Log in as a non-admin user (e.g., tutor)
        self.client.login(username='@tutoruser', password='Password123')

        # Access the ManageTutors view
        response = self.client.get(self.url)

        # Assert that access is forbidden
        self.assertEqual(response.status_code, 403)

    def test_manage_tutors_get_by_anonymous(self):
        """Test that an anonymous user cannot access the ManageTutors view."""
        # Access the ManageTutors view without logging in
        response = self.client.get(self.url)

        # Assert that the user is redirected to the login page
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith('/log_in/'))
