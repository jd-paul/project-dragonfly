from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import timedelta
from django.utils import timezone
from tutorials.models import User, TicketStatus, Ticket, StudentRequest, Term, Frequency, Enrollment, Skill


class ManageTicketsViewTestCase(TestCase):
    """Test admins managing students' and tutors' tickets"""
    fixtures = ['tutorials/tests/fixtures/other_users.json']

    def setUp(self):
        self.admin = User.objects.get(username='@adminuser')
        self.student = User.objects.get(username='@studentuser')
        self.tutor = User.objects.get(username='@tutoruser')
        self.client.login(username='@adminuser', password='Password123')

        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=Skill.objects.create(language='Ruby', level='Advanced'),
            duration=10,
            first_term= Term.JANUARY_EASTER,
            frequency= Frequency.WEEKLY
        )

        # Enrollments
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            tutor=self.tutor,
            current_term=self.student_request.first_term,
            week_count=10,
            start_time=timezone.now(),
            status='ongoing'
        )

        self.pending_ticket = Ticket.objects.create(
            user=self.student, 
            enrollment=self.enrollment, 
            ticket_type='cancellation', 
            description='I want to cancel', 
            status='Pending'
            )
        self.approved_ticket = Ticket.objects.create(
            user=self.tutor, 
            enrollment=self.enrollment, 
            ticket_type='change', 
            description='I want to cancel', 
            status='Approved'
            )
        self.rejected_ticket = Ticket.objects.create(
            user=self.tutor, 
            enrollment=self.enrollment, 
            ticket_type='change', 
            description='I want to cancel', 
            status='Approved'
            )

        self.url = reverse('manage_tickets')

    def test_manage_tickets_get_by_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_tickets.html')
        self.assertIn('new_tickets', response.context)
        self.assertIn('resolved_tickets', response.context)
        self.assertIn(self.pending_ticket, response.context['new_tickets'])
        self.assertIn(self.approved_ticket, response.context['resolved_tickets'])
        self.assertIn(self.rejected_ticket, response.context['resolved_tickets'])


    def test_manage_tickets_get_by_non_admin(self):
        """Non-student users should not access ManageTickets."""
         # Test with student user
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403) 

        # Test with tutor user
        self.client.login(username='@tutoruser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_manage_tickets_get_by_anonymous(self):
        """Anonymous users should not access ManageTickets."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_sees_empty_ticket_lists(self):
        """Admin sees empty lists when there are no tickets."""
        # Delete all tickets
        Ticket.objects.all().delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No new tickets available.")
        self.assertContains(response, "No resolved tickets available.")


    def test_approve_ticket(self):
        """Admin can approve any ticket."""
        post_data = {
            'ticket_id': self.pending_ticket.id,
            'action': 'approve'
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, self.url)
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.APPROVED)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("has been approved", str(messages[0]))

    def test_reject_ticket(self):
        """Admin can reject any ticket."""
        post_data = {
            'ticket_id': self.approved_ticket.id,
            'action': 'reject'
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, self.url)
        self.approved_ticket.refresh_from_db()
        self.assertEqual(self.approved_ticket.status, TicketStatus.REJECTED)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("has been rejected", str(messages[0]))


    def test_invalid_action(self):
        """Admin receives error when performing an invalid action."""
        post_data = {
            'ticket_id': self.pending_ticket.id,
            'action': 'invalid_action'
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, self.url)
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)  

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Invalid action. Please try again.", str(messages[0]))

    def test_missing_ticket_id(self):
        """Admin receives error when ticket_id is missing."""
        post_data = {
            'action': 'approve'
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, self.url)
        # Ensure no ticket status changes
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Invalid request.", str(messages[0]))

    def test_missing_action(self):
        """Admin receives error when action is missing."""
        post_data = {
            'ticket_id': self.pending_ticket.id
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, self.url)
        # Ensure no ticket status changes
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Invalid request.", str(messages[0]))

    def test_non_admin_cannot_approve_ticket(self):
        """Non-admin users should not be able to approve tickets."""
        # Attempt as student user
        self.client.logout()
        self.client.login(username='@studentuser', password='Password123')
        post_data = {
            'ticket_id': self.pending_ticket.id,
            'action': 'approve'
        }
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 403) 
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

        # Attempt as tutor user
        self.client.logout()
        self.client.login(username='@tutoruser', password='Password123')
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 403)
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

    def test_anonymous_user_cannot_approve_ticket(self):
        """Anonymous users should be redirected to login when attempting to approve tickets."""
        self.client.logout()
        post_data = {
            'ticket_id': self.pending_ticket.id,
            'action': 'approve'
        }
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

    def test_post_with_nonexistent_ticket_id(self):
        """Admin receives 404 when ticket_id does not exist."""
        post_data = {
            'ticket_id': 9999, 
            'action': 'approve'
        }
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 404)
        # Ensure no ticket status changes
        self.pending_ticket.refresh_from_db()
        self.assertEqual(self.pending_ticket.status, TicketStatus.PENDING)

    def test_ticket_str_method(self):
        """Ensure the __str__ method of Ticket returns the correct string."""
        expected_str = f"Ticket submitted by {self.pending_ticket.user} - {self.pending_ticket.ticket_type}"
        self.assertEqual(str(self.pending_ticket), expected_str)

    def test_ticket_ordering(self):
        """Ensure tickets are ordered by created_at descending."""
        # Create another pending ticket with a later created_at
        later_ticket = Ticket.objects.create(
            user=self.student,
            enrollment=self.enrollment,
            ticket_type='cancellation',
            description='Another cancellation request.',
            status=TicketStatus.PENDING,
            created_at=timezone.now()
        )

        tickets = Ticket.objects.all()
        self.assertEqual(tickets.first(), later_ticket)
        self.assertEqual(tickets.last(), self.pending_ticket)

