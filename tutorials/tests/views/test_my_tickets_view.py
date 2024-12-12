from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models import Enrollment, Ticket, TicketStatus, StudentRequest, Skill, Term, Frequency

class MyTicketsViewTests(TestCase):

    def setUp(self):
        # Use get_user_model() to dynamically get the custom User model
        User = get_user_model()

        # Create users (student, tutor, admin) with unique email addresses
        self.student_user = User.objects.create_user(
            username='student', 
            email='student@example.com',  # Ensure unique email
            password='password'
        )
        self.tutor_user = User.objects.create_user(
            username='tutor', 
            email='tutor@example.com',  # Ensure unique email
            password='password'
        )
        self.admin_user = User.objects.create_user(
            username='admin', 
            email='admin@example.com',  # Ensure unique email
            password='password'
        )

        # Create a Skill instance
        self.skill = Skill.objects.create(language='Python', level='Intermediate')

        # Create a StudentRequest instance (use correct field names for duration, first_term, and frequency)
        self.student_request = StudentRequest.objects.create(
            student=self.student_user,  # Correct field name for student
            skill=self.skill,            # Correct field name for skill
            duration=10,                 # Example value for duration
            first_term=Term.SEPTEMBER_CHRISTMAS,  # Example value for first_term
            frequency=Frequency.WEEKLY,  # Example value for frequency
            status='approved'            # Assuming you want the request to be approved
        )

        # Set a timezone-aware datetime for start_time
        start_time = timezone.make_aware(timezone.datetime(2024, 1, 1, 10, 0, 0))

        # Create an Enrollment instance with the StudentRequest
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,  # Correct reference to StudentRequest
            tutor=self.tutor_user,
            current_term=Term.SEPTEMBER_CHRISTMAS,
            week_count=10,
            start_time=start_time,
            status='ongoing'
        )

    def test_my_tickets(self):
        """Test that a user can see their tickets."""
        # Create tickets for the user
        self.client.login(username='student', password='password')
        ticket1 = Ticket.objects.create(
            user=self.student_user,
            enrollment=self.enrollment,
            ticket_type='cancellation',  # or 'change', depending on your test
            description="Message 1",  # Use the description field instead of 'message'
            status=TicketStatus.PENDING
        )
        ticket2 = Ticket.objects.create(
            user=self.student_user,
            enrollment=self.enrollment,
            ticket_type='cancellation',  # or 'change', depending on your test
            description="Message 2",  # Use the description field instead of 'message'
            status=TicketStatus.PENDING
        )

        url = reverse('my_tickets')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ticket1.description)  # Check if ticket description is in the response
        self.assertContains(response, ticket2.description)  # Check if ticket description is in the response
        self.assertContains(response, 'Tickets')  # Check if the word "Tickets" is in the page content

    def test_my_tickets_no_tickets(self):
        """Test that when a user has no tickets, no tickets are shown."""
        self.client.login(username='student', password='password')
        url = reverse('my_tickets')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for the 'No tickets found' message
        self.assertContains(response, 'No tickets found')
