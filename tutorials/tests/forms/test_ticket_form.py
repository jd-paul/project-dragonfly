from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from tutorials.models import Skill, UserType, Enrollment, Ticket, TicketStatus, StudentRequest
from tutorials.forms import TicketForm

class TicketFormTest(TestCase):

    def setUp(self):
        # Create users
        self.student = get_user_model().objects.create_user(
            username="@studentuser", email="student@example.com", password="testpassword", user_type=UserType.STUDENT)
        self.tutor = get_user_model().objects.create_user(
            username="@tutoruser", email="tutor@example.com", password="testpassword", user_type=UserType.TUTOR)

        # Create a skill
        self.skill = Skill.objects.create(language="Math", level="Beginner")

        # Create a student request
        self.student_request = StudentRequest.objects.create(
            student=self.student, skill=self.skill, duration=60, first_term="September-Christmas", frequency="weekly")

        # Create an enrollment for the student
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request, tutor=self.tutor, current_term="September-Christmas", 
            week_count=10, start_time=timezone.now(), status="ongoing")

    def test_ticket_form_valid(self):
        """Test that the form is valid with correct data."""
        form_data = {
            'ticket_type': 'cancellation',
            'description': 'Request to cancel the session.',
            'enrollment': self.enrollment.id,  # Ensure enrollment ID is passed correctly
        }
        form = TicketForm(data=form_data)

        # Ensure the form is valid
        self.assertTrue(form.is_valid())

        # Save the form and check that a ticket is created
        ticket = form.save(commit=False)
        ticket.enrollment = self.enrollment
        ticket.user = self.student  # Assign the ticket to the student (requesting user)
        ticket.status = TicketStatus.PENDING
        ticket.save()

        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(ticket.ticket_type, 'cancellation')
        self.assertEqual(ticket.description, 'Request to cancel the session.')
        self.assertEqual(ticket.status, TicketStatus.PENDING)

    def test_ticket_form_invalid_missing_description(self):
        """Test that the form is invalid if the description is missing."""
        form_data = {
            'ticket_type': 'cancellation',
            'description': '',  # Missing description
            'enrollment': self.enrollment.id,
        }
        form = TicketForm(data=form_data)

        # Ensure the form is invalid
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)  # The error should be for description

    def test_ticket_form_invalid_enrollment(self):
        """Test that the form is invalid if the enrollment doesn't exist or is incorrect."""
        invalid_enrollment_id = 9999  # Assume this ID doesn't exist in the database
        form_data = {
            'ticket_type': 'change',
            'description': 'Request to change the schedule.',
            'enrollment': invalid_enrollment_id,
        }
        form = TicketForm(data=form_data)

        # Ensure the form is invalid
        self.assertFalse(form.is_valid())
        self.assertIn('enrollment', form.errors)  # The error should be for enrollment not being valid

    def test_ticket_form_invalid_user_permission(self):
        """Test that a user who is neither the student nor tutor for the enrollment cannot submit a ticket."""
        unauthorized_user = get_user_model().objects.create_user(
            username="@unauthorized", email="unauthorized@example.com", password="testpassword", user_type=UserType.STUDENT)

        form_data = {
            'ticket_type': 'cancellation',
            'description': 'Request to cancel the session.',
            'enrollment': self.enrollment.id,
        }
        form = TicketForm(data=form_data)

        # Simulate an unauthorized user submitting the form
        self.client.login(username='unauthorized', password='testpassword')
        response = self.client.post(reverse('submit_ticket', args=[self.enrollment.id]), data=form_data)

        # The user should not be able to submit the ticket
        self.assertEqual(response.status_code, 403)  # Expecting a Forbidden response
