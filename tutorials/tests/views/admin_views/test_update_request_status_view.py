from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models import (
    UserType, Skill, StudentRequest, TutorSkill, Enrollment, Invoice, User
)
from datetime import timedelta

User = get_user_model()


class LessonRequestDetailsViewTests(TestCase):
    """Tests for the LessonRequestDetails view."""

    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        # Use existing users from the fixture
        self.admin_user = User.objects.get(username='@adminuser')  # Admin user
        self.student1 = User.objects.get(username='@studentuser')  # Student user
        self.tutor = User.objects.get(username='@tutoruser')      # Tutor user

        # Skill
        self.skill = Skill.objects.create(language="Python", level="Beginner")

        # Valid student request
        self.lesson_request = StudentRequest.objects.create(
            student=self.student1,
            skill=self.skill,
            duration=60,
            status="pending",
            first_term="January-Easter",
            created_at=timezone.now(),
        )

        # Assign skill to tutor
        TutorSkill.objects.create(tutor=self.tutor, skill=self.skill)

        # Another tutor without the required skill
        self.tutor_without_skill = User.objects.create_user(
            username='@noskilltutor',
            password='Password123',
            user_type=UserType.TUTOR,
            first_name='NoSkill',
            last_name='Tutor',
            email='noskill@example.com',
        )

        # URL for lesson request details
        self.url = reverse('lesson_request_details', args=[self.lesson_request.id])

    def login_as_admin(self):
        """Helper method to log in as admin user."""
        self.client.login(username='@adminuser', password='Password123')

    def test_assign_tutor_creates_new_enrollment(self):
        """Test assigning a tutor creates a new enrollment."""
        self.login_as_admin()
        response = self.client.get(self.url, {'assign_tutor': self.tutor.id})
        self.assertRedirects(response, self.url)

        # Check if an enrollment is created
        enrollment = Enrollment.objects.filter(approved_request=self.lesson_request).first()
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.tutor, self.tutor)
        self.assertEqual(enrollment.status, 'ongoing')

        # Check if an invoice is created
        invoice = Invoice.objects.filter(enrollment=enrollment).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, 0.00)