from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import UserType, PendingTutor, Skill, SkillLevel, TutorSkill

User = get_user_model()

class ManageTutorsViewTests(TestCase):
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
        self.assertContains(response, "Invalid action. Please try again.")

    def test_manage_tutors_post_invalid_request(self):
        """Test POST request with missing tutor_id or action."""
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Invalid request.")
