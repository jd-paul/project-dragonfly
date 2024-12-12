from django.test import TestCase, Client
from django.urls import reverse

from tutorials.models import (
    User, Enrollment, StudentRequest, Skill, Invoice,
    Term, UserType, TutorSkill
)
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class TutorEnrollmentListTests(TestCase):
    fixtures = ['tutorials/tests/fixtures/other_users.json']
    def setUp(self):
        self.client = Client()
        
        self.tutor = User.objects.get(username='@tutoruser')
        self.other_tutor = User.objects.get(username='@petrapickles')
        self.student = User.objects.get(username='@studentuser')
        self.admin = User.objects.get(username='@adminuser')
        
        # Create skills
        self.skill_python = Skill.objects.create(
            language='Python',
            level='Advanced'
        )
        self.skill_django = Skill.objects.create(
            language='Django',
            level='Intermediate'
        )
        
        # Assign TutorSkill to tutor
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
        
        # Create StudentRequest
        self.student_request_python = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_python,
            duration=90,
            first_term=Term.JANUARY_EASTER,
            frequency='weekly',
            status='approved'
        )
        self.student_request_django = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_django,
            duration=60,
            first_term=Term.MAY_JULY,
            frequency='bi-weekly',
            status='approved'
        )
        
        # Create Enrollments
        self.enrollment_python = Enrollment.objects.create(
            approved_request=self.student_request_python,
            tutor=self.tutor,
            current_term=Term.JANUARY_EASTER,
            week_count=10,
            start_time=timezone.now(),
            status='ongoing'
        )
        self.enrollment_django = Enrollment.objects.create(
            approved_request=self.student_request_django,
            tutor=self.tutor,
            current_term=Term.MAY_JULY,
            week_count=8,
            start_time=timezone.now(),
            status='ongoing'
        )
        
        # Create Invoices
        self.invoice_python = Invoice.objects.create(
            enrollment=self.enrollment_python,
            amount=Decimal('1500.00'),
            issued_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            payment_status='unpaid'
        )
        self.invoice_django = Invoice.objects.create(
            enrollment=self.enrollment_django,
            amount=Decimal('1200.00'),
            issued_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            payment_status='unpaid'
        )
        
        # Reverse URL
        self.url = reverse('tutor_enrollments')

    def test_tutor_enrollments_accessible_by_tutor(self):
        """Test that a tutor can access their enrollments view."""
        login = self.client.login(username='@tutoruser', password='Password123')
        self.assertTrue(login, "Login failed for @tutoruser.")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor/tutor_enrollments.html')
        self.assertIn('enrollments', response.context)
        
        enrollments = response.context['enrollments']
        self.assertEqual(len(enrollments), 2)
        self.assertIn(self.enrollment_python, enrollments)
        self.assertIn(self.enrollment_django, enrollments)

    def test_tutor_enrollments_denies_access_to_non_tutor(self):
        """Test that non-tutor users cannot access the tutor enrollments view."""
        # Login as student
        login = self.client.login(username='@studentuser', password='Password123')
        self.assertTrue(login, "Login failed for @studentuser.")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        
        # Login as admin
        self.client.logout()
        login = self.client.login(username='@adminuser', password='Password123')
        self.assertTrue(login, "Login failed for @adminuser.")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_tutor_enrollments_redirects_anonymous_user(self):
        """Test that an anonymous user is redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_tutor_enrollments_only_shows_tutor_specific_enrollments(self):
        """Test that a tutor sees only their own enrollments."""
        # Create another tutor and enrollment
        another_tutor = User.objects.create_user(
            username='@othertutor',
            password='Password123',
            user_type=UserType.TUTOR
        )
        TutorSkill.objects.create(
            tutor=another_tutor,
            skill=self.skill_python,
            price_per_hour=Decimal('55.00')
        )
        student_request_other = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill_python,
            duration=120,
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency='weekly',
            status='approved'
        )
        enrollment_other = Enrollment.objects.create(
            approved_request=student_request_other,
            tutor=another_tutor,
            current_term=Term.SEPTEMBER_CHRISTMAS,
            week_count=12,
            start_time=timezone.now(),
            status='ongoing'
        )
        Invoice.objects.create(
            enrollment=enrollment_other,
            amount=Decimal('1800.00'),
            issued_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            payment_status='unpaid'
        )
        
        # Login as original tutor
        self.client.logout()
        login = self.client.login(username='@tutoruser', password='Password123')
        self.assertTrue(login, "Login failed for @tutoruser.")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        enrollments = response.context['enrollments']
        self.assertEqual(len(enrollments), 2)
        self.assertIn(self.enrollment_python, enrollments)
        self.assertIn(self.enrollment_django, enrollments)
        self.assertNotIn(enrollment_other, enrollments)

    def test_tutor_enrollments_empty_list(self):
        """Test that the enrollments view handles tutors with no enrollments gracefully."""
        # Create a new tutor with no enrollments
        new_tutor = User.objects.create_user(
            username='@newtutor',
            password='Password123',
            user_type=UserType.TUTOR
        )
        TutorSkill.objects.create(
            tutor=new_tutor,
            skill=self.skill_python,
            price_per_hour=Decimal('55.00')
        )
        
        # Reverse URL for the new tutor
        url_new_tutor = reverse('tutor_enrollments')
        
        # Login as new tutor
        self.client.logout()
        login = self.client.login(username='@newtutor', password='Password123')
        self.assertTrue(login, "Login failed for @newtutor.")
        
        response = self.client.get(url_new_tutor)
        self.assertEqual(response.status_code, 200)
        enrollments = response.context['enrollments']
        self.assertEqual(len(enrollments), 0)

    def test_tutor_enrollments_correct_context_data(self):
        """Test that the context data in the enrollments view is correct."""
        login = self.client.login(username='@tutoruser', password='Password123')
        self.assertTrue(login, "Login failed for @tutoruser.")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        enrollments = response.context['enrollments']
        
        for enrollment in enrollments:
            self.assertEqual(enrollment.tutor, self.tutor)
            self.assertTrue(hasattr(enrollment, 'approved_request'))
            self.assertEqual(enrollment.approved_request.status, 'approved')
