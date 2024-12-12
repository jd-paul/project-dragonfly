from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import UserType, PendingTutor, Skill, SkillLevel, TutorSkill, User


class ManageTutorsViewTests(TestCase):
    User = get_user_model()
    @classmethod
    def setUpTestData(cls):
        # Create admin user
        cls.admin_user = User.objects.create_user(
            username="admin", 
            email="admin@example.com", 
            password="password123", 
            user_type=UserType.ADMIN
        )

        # Create a pending tutor
        cls.pending_tutor_user = User.objects.create_user(
            username="pending_tutor",
            email="pending_tutor@example.com",
            password="password123",
            user_type=UserType.PENDING
        )
        cls.pending_tutor = PendingTutor.objects.create(
            user=cls.pending_tutor_user,
            price_per_hour=30.00
        )

        # Add a skill to the pending tutor
        cls.skill = Skill.objects.create(language="Python", level=SkillLevel.INTERMEDIATE)
        cls.pending_tutor.skills.add(cls.skill)

        # Create an approved tutor
        cls.tutor_user = User.objects.create_user(
            username="approved_tutor",
            email="approved_tutor@example.com",
            password="password123",
            user_type=UserType.TUTOR,
            is_active=True
        )
        cls.tutor_skill = TutorSkill.objects.create(
            tutor=cls.tutor_user,
            skill=cls.skill,
            price_per_hour=50.00
        )

        # URL for the view
        cls.url = reverse('manage_tutors')

    def setUp(self):
        # Log in as admin for all tests
        self.client = Client()
        self.client.login(username="admin", password="password123")

    def test_manage_tutors_get(self):
        """Test GET request to display pending and approved tutors."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tutors.html')

        # Check pending tutors in context
        pending_tutors = response.context['tutors']
        self.assertIn(self.pending_tutor, pending_tutors)

        # Check approved tutors in context
        current_tutors = response.context['current_tutors']
        self.assertIn(self.tutor_user, current_tutors)

        # Check counts
        self.assertEqual(response.context['tutor_count'], 1)
        self.assertEqual(response.context['current_tutors_count'], 1)

    def test_manage_tutors_post_approve(self):
        """Test POST request to approve a pending tutor."""
        response = self.client.post(self.url, data={
            'tutor_id': self.pending_tutor.id,
            'action': 'approve'
        })

        self.assertRedirects(response, self.url)

        # Check that the user is now a TUTOR
        self.pending_tutor_user.refresh_from_db()
        self.assertEqual(self.pending_tutor_user.user_type, UserType.TUTOR)
        self.assertTrue(self.pending_tutor_user.is_active)

        # Check TutorSkill created
        self.assertTrue(
            TutorSkill.objects.filter(
                tutor=self.pending_tutor_user,
                skill=self.skill,
                price_per_hour=self.pending_tutor.price_per_hour
            ).exists()
        )

        # Check pending tutor is approved
        self.pending_tutor.refresh_from_db()
        self.assertTrue(self.pending_tutor.is_approved)

    def test_manage_tutors_post_reject(self):
        """Test POST request to reject a pending tutor."""
        response = self.client.post(self.url, data={
            'tutor_id': self.pending_tutor.id,
            'action': 'reject'
        })

        self.assertRedirects(response, self.url)

        # Check that the PendingTutor is deleted
        with self.assertRaises(PendingTutor.DoesNotExist):
            self.pending_tutor.refresh_from_db()

    def test_manage_tutors_post_invalid_action(self):
        """Test POST request with an invalid action."""
        response = self.client.post(self.url, data={
            'tutor_id': self.pending_tutor.id,
            'action': 'invalid_action'
        })

        self.assertRedirects(response, self.url)


    def test_manage_tutors_post_invalid_request(self):
        """Test POST request with missing tutor_id or action."""
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, self.url)



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
