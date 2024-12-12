from django.test import TestCase
from django.utils import timezone
from tutorials.models import Term, Skill, User, StudentRequest, Enrollment, Ticket
from tutorials.forms import TicketForm

class TicketFormTest(TestCase):
    def setUp(self):
        # Create necessary objects
        self.student = User.objects.create_user(
            username='@studentuser', email='student@example.com', password='password123'
        )
        self.tutor = User.objects.create_user(
            username='@tutoruser', email='tutor@example.com', password='password123'
        )

        # Create a skill for the enrollment
        self.skill = Skill.objects.create(language="Python", level="Beginner")

        # Create a student request
        student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=60,
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency="weekly"
        )

        # Create an enrollment instance
        self.enrollment = Enrollment.objects.create(
            approved_request=student_request,
            tutor=self.tutor,
            current_term=Term.SEPTEMBER_CHRISTMAS,
            week_count=10,
            status="ongoing",
            start_time=timezone.now()  # Ensure the start_time uses timezone.now()
        )

        # Initialize the form data
        self.valid_data = {
            'ticket_type': 'cancellation',  # Example ticket type
            'description': 'Test ticket description',  # Example description
            'enrollment': self.enrollment  # Pass the valid enrollment object
        }

    def test_save_creates_ticket(self):
        """Test that saving the form creates a Ticket object."""
        form = TicketForm(data=self.valid_data)
        self.assertTrue(form.is_valid())  # Ensure the form is valid
        ticket = form.save()  # Save the form and create the ticket
        self.assertEqual(Ticket.objects.count(), 1)  # Check if one ticket is created
        self.assertEqual(ticket.enrollment, self.enrollment)  # Ensure ticket is associated with the correct enrollment

    def test_invalid_ticket_form_missing_description(self):
        """Test that the form is invalid if the description is missing."""
        invalid_data = {
            'ticket_type': 'cancellation',
            'description': '',  # Missing description
            'enrollment': self.enrollment
        }
        form = TicketForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_valid_ticket_form(self):
        """Test that the form is valid with correct data."""
        form = TicketForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
