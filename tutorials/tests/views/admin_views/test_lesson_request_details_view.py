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

    def test_assign_tutor_updates_existing_enrollment(self):
        """Test assigning a tutor updates an existing enrollment."""
        # Create an initial enrollment
        existing_enrollment = Enrollment.objects.create(
            approved_request=self.lesson_request,
            tutor=self.tutor,
            current_term=self.lesson_request.first_term,
            week_count=12,
            start_time=timezone.now(),
            status="ongoing",
        )

        # Assign a new tutor
        new_tutor = User.objects.create_user(
            username='@newtutor',
            password='Password123',
            user_type=UserType.TUTOR,
            first_name='New',
            last_name='Tutor',
            email='newtutor@example.com',
        )
        TutorSkill.objects.create(tutor=new_tutor, skill=self.skill)

        self.login_as_admin()
        response = self.client.get(self.url, {'assign_tutor': new_tutor.id})
        self.assertRedirects(response, self.url)

        # Check if the enrollment is updated
        existing_enrollment.refresh_from_db()
        self.assertEqual(existing_enrollment.tutor, new_tutor)

    def test_assign_invalid_tutor_returns_404(self):
        """Test assigning an invalid tutor returns a 404 error."""
        self.login_as_admin()

        # Invalid tutor ID
        invalid_tutor_id = 9999
        response = self.client.get(self.url, {'assign_tutor': invalid_tutor_id})
        self.assertEqual(response.status_code, 404)

    def test_assign_tutor_updates_existing_enrollment_with_required_skill(self):
        """Test assigning a tutor with the required skill updates an existing enrollment."""
        # Create an initial enrollment with the first tutor
        existing_enrollment = Enrollment.objects.create(
            approved_request=self.lesson_request,
            tutor=self.tutor,
            current_term=self.lesson_request.first_term,
            week_count=12,
            start_time=timezone.now(),
            status="ongoing",
        )

        # Create a new tutor with the required skill
        new_tutor = User.objects.create_user(
            username='@newtutor',
            password='Password123',
            user_type=UserType.TUTOR,
            first_name='New',
            last_name='Tutor',
            email='newtutor@example.com',
        )
        TutorSkill.objects.create(tutor=new_tutor, skill=self.skill)

        self.login_as_admin()
        response = self.client.get(self.url, {'assign_tutor': new_tutor.id})
        self.assertRedirects(response, self.url)

        # Check if the enrollment is updated
        existing_enrollment.refresh_from_db()
        self.assertEqual(existing_enrollment.tutor, new_tutor)