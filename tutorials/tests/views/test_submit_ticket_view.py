from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from tutorials.models import Ticket, Enrollment, StudentRequest, Skill, Term, Frequency, TicketStatus

class SubmitTicketViewTests(TestCase):

    def setUp(self):
        User = get_user_model()

        # Create test users (student, tutor, admin) with unique emails
        self.student_user = User.objects.create_user(username='student', email='student@example.com', password='password')
        self.tutor_user = User.objects.create_user(username='tutor', email='tutor@example.com', password='password')

        # Create a Skill instance
        self.skill = Skill.objects.create(language='Python', level='Intermediate')

        # Create a StudentRequest instance
        self.student_request = StudentRequest.objects.create(
            student=self.student_user,
            skill=self.skill,
            duration=10,
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY,
            status='approved'
        )

        # Create an Enrollment instance
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            tutor=self.tutor_user,
            current_term=Term.SEPTEMBER_CHRISTMAS,
            week_count=10,
            start_time="2024-01-01 10:00:00",
            status='ongoing'
        )

    def test_submit_ticket_as_student(self):
        """Test that the student can submit a ticket."""
        self.client.login(username='student', password='password')
        
        # Define the URL for submitting a ticket
        url = reverse('submit_ticket', args=[self.enrollment.id])
        
        # Create ticket data
        data = {
            'ticket_type': 'cancellation',
            'description': 'Need to cancel the session.',
            'status': TicketStatus.PENDING,
        }
        
        # Submit the form as the student
        response = self.client.post(url, data)
        
        # Check that the ticket was created and the response is correct
        self.assertEqual(response.status_code, 302)  # Should redirect after successful submission
        ticket = Ticket.objects.first()
        self.assertEqual(ticket.user, self.student_user)
        self.assertEqual(ticket.enrollment, self.enrollment)
        self.assertEqual(ticket.ticket_type, 'cancellation')

    def test_submit_ticket_as_tutor(self):
        """Test that the tutor can submit a ticket."""
        self.client.login(username='tutor', password='password')

        # Define the URL for submitting a ticket
        url = reverse('submit_ticket', args=[self.enrollment.id])
        
        # Create ticket data
        data = {
            'ticket_type': 'cancellation',
            'description': 'Need to reschedule the session.',
            'status': TicketStatus.PENDING,
        }

        # Submit the form as the tutor
        response = self.client.post(url, data)

        # Check that the ticket was created and the response is correct
        self.assertEqual(response.status_code, 302)  # Should redirect after successful submission
        ticket = Ticket.objects.first()
        self.assertEqual(ticket.user, self.tutor_user)
        self.assertEqual(ticket.enrollment, self.enrollment)
        self.assertEqual(ticket.ticket_type, 'cancellation')
   
    def test_submit_ticket_invalid_form(self):
        """Test submitting an invalid ticket form."""
        self.client.login(username='student', password='password')

        # Define the URL for submitting a ticket
        url = reverse('submit_ticket', args=[self.enrollment.id])

        # Create invalid ticket data (missing description)
        data = {
            'ticket_type': 'cancellation',
            'status': TicketStatus.PENDING,
        }

        # Submit the invalid form
        response = self.client.post(url, data)

        # Check that the form is invalid and re-renders
        self.assertEqual(response.status_code, 200)  # Should return the form again with errors
        
        # Ensure the context contains the form
        form = response.context.get('form')
        self.assertIsNotNone(form, "The form should be in the response context.")
        
        # Check that the form has an error on the 'description' field
        self.assertTrue(form.errors, "The form should contain errors.")
        self.assertIn('description', form.errors, "The 'description' field should have an error.")

    def test_submit_ticket_permission_denied(self):
        """Test that only the respective student or tutor can submit a ticket."""
        # Create another user who is neither the student nor tutor for this enrollment
        other_user = get_user_model().objects.create_user(username='otheruser', email='otheruser@example.com', password='password')
        self.client.login(username='otheruser', password='password')

        # Define the URL for submitting a ticket
        url = reverse('submit_ticket', args=[self.enrollment.id])

        # Try to submit a ticket as the other user
        data = {
            'ticket_type': 'cancellation',
            'description': 'This should not be allowed.',
            'status': TicketStatus.PENDING,
        }

        # Submit the form and check for permission denial (403 Forbidden)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)  # Permission Denied should be a 403 error
