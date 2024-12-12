from django.test import TestCase
from django.urls import reverse
from tutorials.models import User, PendingTutor, TutorSkill, Skill, UserType
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger

class ManageTutorsViewTestCase(TestCase):
    """Test the ManageTutors view."""
    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Admin user
        self.admin = User.objects.get(username='@adminuser')

        # Approved Tutor user
        self.tutor = User.objects.get(username='@tutoruser')

        # Pending Tutor user (create a separate user)
        self.pending_tutor_user = User.objects.create_user(
            username='@pendingtutor',
            email='pendingtutor@example.com',
            password='Password123',
            user_type=UserType.TUTOR,
            is_active=False  # Pending tutors are typically inactive
        )

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
            user=self.pending_tutor_user,
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

    def test_manage_tutors_page_not_an_integer(self):
        """Test that the view handles a 'PageNotAnInteger' exception."""
        # Log in as admin
        self.client.login(username='@adminuser', password='Password123')

        # Access the view with an invalid page number (non-integer)
        response = self.client.get(self.url, {'page': 'invalid'})

        # Assert correct status code and template usage
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tutors.html')

        # Assert that it defaults to the first page
        tutors = response.context['tutors']
        self.assertEqual(tutors.number, 1)

    def test_manage_tutors_empty_page(self):
        """Test that the view handles an 'EmptyPage' exception."""
        # Log in as admin
        self.client.login(username='@adminuser', password='Password123')

        # Access the view with a page number beyond the last page
        response = self.client.get(self.url, {'page': 999})

        # Assert correct status code and template usage
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tutors.html')

        # Assert that it defaults to the last page
        tutors = response.context['tutors']
        self.assertEqual(tutors.number, tutors.paginator.num_pages)
