from django.test import TestCase
from django.urls import reverse

from tutorials.models import (
    User, Enrollment, StudentRequest, Skill, Invoice,
    Term,  TutorSkill
)
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class YourEnrollmentsViewTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']
    def setUp(self):

        self.student = User.objects.get(username='@studentuser')
        self.other_student = User.objects.get(username='@peterpickles')
        self.admin = User.objects.get(username='@adminuser')
        self.tutor = User.objects.get(username='@tutoruser')

        self.skill_python = Skill.objects.create(
            language='Python',
            level='Advanced'
        )
        self.skill_django = Skill.objects.create(
            language='Django',
            level='Intermediate'
        )

        self.tutor_skill_python = TutorSkill.objects.create(
            tutor=self.tutor,
            skill=self.skill_python,
            price_per_hour=Decimal('50.00')
        )
        self.tutor_skill_django = TutorSkill.objects.create(
            tutor=self.tutor,
            skill=self.skill_django,
            price_per_hour=Decimal('60.00')
        )

        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_python,
            duration=90,
            first_term=Term.JANUARY_EASTER,
            frequency='weekly',
            status='approved'
        )
 
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            tutor=self.tutor,
            current_term=Term.JANUARY_EASTER,
            week_count=10,
            start_time=timezone.now(),
            status='ongoing'
        )

        self.invoice = Invoice.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('1500.00'),
            issued_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            payment_status='unpaid'
        )

        self.url = reverse('your_enrollments')

    def test_your_enrollments_accessible_by_student(self):
        """Test that a student can access their enrollments view."""
        self.client.login(username='@studentuser', password='Password123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/your_enrollments.html')
        self.assertIn('enrollments', response.context)
        
        enrollments = response.context['enrollments']
        self.assertEqual(len(enrollments), 1)
        enrollment = enrollments[0]
        self.assertEqual(enrollment, self.enrollment)
        self.assertTrue(hasattr(enrollment, 'has_invoice'))
        self.assertTrue(enrollment.has_invoice)

    def test_your_enrollments_no_invoice(self):
        """Test that enrollments without an invoice are correctly flagged."""
        # Create another enrollment without an invoice
        student_request_no_invoice = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_django,
            duration=60,
            first_term=Term.MAY_JULY,
            frequency='bi-weekly',
            status='approved'
        )
        enrollment_no_invoice = Enrollment.objects.create(
            approved_request=student_request_no_invoice,
            tutor=self.tutor,
            current_term=Term.MAY_JULY,
            week_count=8,
            start_time=timezone.now(),
            status='ongoing'
        )
        
        self.client.login(username='@studentuser', password='Password123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        enrollments = response.context['enrollments']
        self.assertEqual(len(enrollments), 2)
        
        # Check the new enrollment
        for enrollment in enrollments:
            if enrollment == enrollment_no_invoice:
                self.assertFalse(enrollment.has_invoice)
            elif enrollment == self.enrollment:
                self.assertTrue(enrollment.has_invoice)

    def test_your_enrollments_denies_access_to_non_student(self):
        """Test that non-student users cannot access the enrollments view."""
        # Login as tutor
        self.client.login(username='@tutoruser', password='Password123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        
        # Login as admin
        self.client.logout()
        self.client.login(username='@adminuser', password='Password123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_your_enrollments_redirects_anonymous_user(self):
        """Test that an anonymous user is redirected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_your_enrollments_includes_correct_invoice_flag(self):
        """Test that the 'has_invoice' flag correctly reflects invoice existence."""
        # Already tested in previous test, but adding for clarity
        self.client.login(username='@studentuser', password='Password123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        enrollments = response.context['enrollments']
        
        for enrollment in enrollments:
            if enrollment == self.enrollment:
                self.assertTrue(enrollment.has_invoice)
            else:
                self.assertFalse(enrollment.has_invoice)
