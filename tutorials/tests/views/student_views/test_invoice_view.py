from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import (User, Enrollment, StudentRequest, Skill, Invoice, Term, UserType, TutorSkill)
from django.utils import timezone
from datetime import timedelta






class InvoiceViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']


    def setUp(self):
        self.admin = User.objects.get(username='@adminuser')
        self.student = User.objects.get(username='@studentuser')
        self.tutor = User.objects.get(username='@tutoruser')


        self.skill_python = Skill.objects.create(
            language='Python',
            level='Advanced'
        )


        self.skill_django = Skill.objects.create(
            language='Django',
            level='Intermediate'
        )


        self.tutor_skill = TutorSkill.objects.create(
            skill=self.skill_python,
            tutor=self.tutor,
            price_per_hour=10
        )


        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_python,
            duration=90,
            first_term= Term.JANUARY_EASTER,
            frequency='weekly'
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


        self.invoice = Invoice.objects.create(
            enrollment=self.enrollment,
            amount=1500.00,
            issued_date=timezone.now(),
            due_date=timezone.now()+timedelta(hours=2) ,
            payment_status='unpaid'
        )


        # URL for InvoiceView
        self.url = reverse('invoice', args=[self.enrollment.id])  # Adjust 'invoice' to your URL name


    def test_invoice_view_accessible_by_student(self):
        """Test that a student can access their invoice."""
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/invoice.html')
        self.assertIn('student', response.context)
        self.assertIn('tutor', response.context)
        self.assertIn('start_time', response.context)
        self.assertIn('term', response.context)
        self.assertIn('frequency', response.context)
        self.assertIn('amount', response.context)
        self.assertIn('tutor_skill', response.context)


    def test_invoice_view_redirects_anonymous_user(self):
        """Test that an anonymous user is redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


    def test_invoice_view_denies_access_to_non_student_user(self):
        """Test that non-student users cannot access the invoice view."""
        # Login as tutor
        self.client.login(username='@tutoruser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


        # Login as admin
        self.client.login(username='@adminuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403) 


    def test_invoice_view_with_valid_enrollment(self):
        """Test that the invoice view displays correct data for a valid enrollment."""
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


        # Check context data
        context = response.context
        self.assertEqual(context['student'], self.enrollment.approved_request.student)
        self.assertEqual(context['tutor'], self.enrollment.tutor)
        self.assertEqual(context['start_time'], self.enrollment.start_time)
        self.assertEqual(context['term'], self.enrollment.current_term)
        self.assertEqual(context['frequency'], self.enrollment.approved_request.frequency)
        self.assertEqual(context['amount'], self.enrollment.invoice.subtotal)
        self.assertEqual(context['tutor_skill'], self.enrollment.tutor.skills.get(skill=self.enrollment.approved_request.skill).skill)


    def test_invoice_view_with_invalid_enrollment(self):
        """Test that accessing an invalid enrollment ID returns 404."""
        self.client.login(username='@studentuser', password='Password123')
        invalid_url = reverse('invoice', args=[9999])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)




    def test_invoice_view_missing_invoice(self):
        """Test that enrollment without an invoice raises an error."""
        # Create enrollment without invoice
        student_request_no_invoice = StudentRequest.objects.create(
            student=self.student,
            first_term= Term.JANUARY_EASTER,
            frequency='bi-weekly',
            skill=self.skill_django,
            duration=90
        )


        enrollment_no_invoice = Enrollment.objects.create(
            approved_request=student_request_no_invoice,
            current_term=Term.JANUARY_EASTER,
            tutor=self.tutor,
            week_count=8,
            start_time=timezone.now(),
            status='ongoing'
        )
        url_no_invoice = reverse('invoice', args=[enrollment_no_invoice.id])
        self.client.login(username='@studentuser', password='Password123')
        response = self.client.get(url_no_invoice)
        self.assertEqual(response.status_code, 404)


    def test_invoice_view_only_accessible_by_associated_student(self):
        """Test that only the student associated with the enrollment can access the invoice."""
        # Create another student
        other_student = User.objects.get(username='@peterpickles')
        self.client.login(username='@peterpickles', password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)  # Forbidden


    def test_invoice_view_handles_multiple_enrollments(self):
        """Test that multiple enrollments are handled correctly."""
        # Create another enrollment for the same student
        student_request2 = StudentRequest.objects.create(
            student=self.student,
            first_term= Term.MAY_JULY,
            frequency='bi-weekly',
            skill=self.skill_django,
            duration=90
        )
        enrollment2 = Enrollment.objects.create(
            approved_request=student_request2,
            current_term=Term.MAY_JULY,
            tutor=self.tutor,
            week_count=6,
            start_time=timezone.now(),
            status='ongoing'
        )


        TutorSkill.objects.create(
            skill=self.skill_django,
            tutor=self.tutor,
            price_per_hour=20
        )


        Invoice.objects.create(
            enrollment=enrollment2,
            amount=800.00,
            issued_date=timezone.now(),
            due_date=timezone.now()+timedelta(hours=2) ,
            payment_status='unpaid'
        )
        url2 = reverse('invoice', args=[enrollment2.id])


        # Access first invoice
        self.client.login(username='@studentuser', password='Password123')
        response1 = self.client.get(self.url)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, f"{self.invoice.enrollment.current_term}")


        # Access second invoice
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "May-July")