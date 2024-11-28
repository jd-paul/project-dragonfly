"""Unit tests for the User model."""
from django.test import TestCase
from django.core.exceptions import ValidationError
from  django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from tutorials.models import (
    UserType, User, SkillLevel, Skill, TutorSkill, Term, Frequency,
    Day, StudentRequest, Enrollment, EnrollmentDays, Invoice
)

class SkillModelTestCase(TestCase):
    """Unit tests for the Skill model."""

    def test_skill_unique_constraint(self):
        Skill.objects.create(language='JavaScript', level=SkillLevel.BEGINNER)
        with self.assertRaises(IntegrityError):
            Skill.objects.create(language='JavaScript', level=SkillLevel.BEGINNER)

    def test_language_max_length(self):
        skill = Skill(language='a' * 151, level=SkillLevel.BEGINNER)
        with self.assertRaises(ValidationError):
            skill.full_clean()


class TutorSkillModelTestCase(TestCase):
    """Unit tests for the TutorSkill model."""

    def setUp(self):
        self.tutor = User.objects.create(
            username='@tutorusername1',
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            password='password12345',
            user_type=UserType.TUTOR
            )

        self.skill = Skill.objects.create(
            language='JavaScript',
            level=SkillLevel.INTERMEDIATE
        )

    def test_tutor_skill_creation(self):
        tutor_skill = TutorSkill.objects.create(
            tutor=self.tutor,
            skill=self.skill,
            price_per_hour=50.00
        )

        self.assertEqual(tutor_skill.tutor, self.tutor)
        self.assertEqual(tutor_skill.skill, self.skill)
        self.assertEqual(tutor_skill.price_per_hour, 50.00)

    def test_price_per_hour_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            tutor_skill = TutorSkill(
                tutor=self.tutor,
                skill=self.skill,
                price_per_hour=-10.00
            )
            tutor_skill.full_clean()

    def test_price_per_hour_precision(self):
        """Test that the price cannot have more than two decimals."""
        with self.assertRaises(ValidationError):
            tutor_skill = TutorSkill(
                tutor=self.tutor,
                skill=self.skill,
                price_per_hour=50.005
            )
            tutor_skill.full_clean()

    def test_tutor_skill_unique_constraint(self):
        """Test that a tutor cannot have the same skill assigned twice."""
        TutorSkill.objects.create(
            tutor=self.tutor,
            skill=self.skill,
            price_per_hour=50.00
        )
        with self.assertRaises(IntegrityError):
            TutorSkill.objects.create(
                tutor=self.tutor,
                skill=self.skill,
                price_per_hour=60.00 
            )


class StudentRequestModelTestCase(TestCase):

    def setUp(self):
        self.student = User.objects.create(
            username='@studentusername1',
            first_name='Jack',
            last_name='Doe',
            email='jackdoe@example.com',
            password='password12345',
            user_type=UserType.STUDENT
            )
        
        self.skill = Skill.objects.create(
            language='Python',
            level=SkillLevel.INTERMEDIATE
        )

    def test_student_request_creation(self):
        duration = time(hour=1, minute=30)
        student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=duration,
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY
        )
        self.assertEqual(student_request.student, self.student)
        self.assertEqual(student_request.skill, self.skill)
        self.assertEqual(student_request.duration, duration)
        self.assertEqual(student_request.first_term, Term.SEPTEMBER_CHRISTMAS)
        self.assertEqual(student_request.frequency, Frequency.WEEKLY)

    def test_student_request_created_at_upon_creation(self):
        before_creation_time = timezone.now()
        student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=time(hour=1, minute=30),
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY
        )
        after_creation_time = timezone.now()
        self.assertIsNotNone(student_request.created_at)
        self.assertTrue(before_creation_time <= student_request.created_at <= after_creation_time)

    # todo
    # def test_student_request_created_at_doesnt_change_upon_update(self):
  

class EnrollmentModelTestCase(TestCase):

    def setUp(self):
        self.student = User.objects.create(
            username='@studentusername1',
            first_name='Jack',
            last_name='Doe',
            email='jackdoe@example.com',
            password='password12345',
            user_type=UserType.STUDENT
            )
        
        self.skill = Skill.objects.create(
            language='Python',
            level=SkillLevel.INTERMEDIATE
        )

        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=time(hour=1),
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY
        )

        self.tutor = User.objects.create(
            username='@tutorusername1',
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            password='password1234',
            user_type=UserType.TUTOR
            )
    
    def test_enrollment_creation(self):
        start_time = timezone.now()
        enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            current_term=Term.JANUARY_EASTER, # can be different from term in student request
            tutor=self.tutor,
            start_time=start_time,
            status='ongoing'
        )
        self.assertEqual(enrollment.approved_request, self.student_request)
        self.assertEqual(enrollment.current_term, Term.JANUARY_EASTER)
        self.assertEqual(enrollment.tutor, self.tutor)
        self.assertEqual(enrollment.status, 'ongoing')

    def test_enrollment_created_at_updated_at_upon_creation(self):
        before_creation_time = timezone.now()
        enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            current_term=Term.JANUARY_EASTER, 
            tutor=self.tutor,
            start_time=timezone.now(),
            status='ongoing'
        )
        after_creation_time = timezone.now()
        self.assertIsNotNone(enrollment.created_at)
        self.assertIsNotNone(enrollment.updated_at)
        self.assertTrue(before_creation_time <= enrollment.created_at <= after_creation_time)
        self.assertTrue(before_creation_time <= enrollment.updated_at <= after_creation_time)
        

  # todo
    # def test_enrollment_created_at_doesnt_change_upon_update(self):
    #update does

class EnrollmentDaysModelTestCase(TestCase):

    def setUp(self):
        self.student = User.objects.create(
            username='@studentusername1',
            first_name='Jack',
            last_name='Doe',
            email='jackdoe@example.com',
            password='password12345',
            user_type=UserType.STUDENT
            )
        
        self.skill = Skill.objects.create(
            language='Python',
            level=SkillLevel.INTERMEDIATE
        )

        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=time(hour=1),
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY
        )

        self.tutor = User.objects.create(
            username='@tutorusername1',
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            password='password1234',
            user_type=UserType.TUTOR
            )
        
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            current_term=Term.JANUARY_EASTER, 
            tutor=self.tutor,
            start_time=timezone.now(),
            status='ongoing'
        )

        self.monday = Day.objects.create(day_name='Monday')
        self.tuesday = Day.objects.create(day_name='Tuesday')

    def test_enrollment_days_multiple_days_creation(self):
        EnrollmentDays.objects.create(
            day_name=self.monday,
            enrollment=self.enrollment
        )
        EnrollmentDays.objects.create(
            day_name=self.tuesday,
            enrollment=self.enrollment
        )
        days = self.enrollment.days.all()
        self.assertEqual(days.count(), 2)
        self.assertIn(self.monday, [day.day_name for day in days])
        self.assertIn(self.tuesday, [day.day_name for day in days])

    def test_unique_constraint_on_enrollment_days(self):
        EnrollmentDays.objects.create(
            day_name=self.monday,
            enrollment=self.enrollment
        )
        with self.assertRaises(IntegrityError):
            EnrollmentDays.objects.create(
                day_name=self.monday,
                enrollment=self.enrollment
            )

class InvoiceModelTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create(
            username='@studentusername1',
            first_name='Jack',
            last_name='Doe',
            email='jackdoe@example.com',
            password='password12345',
            user_type=UserType.STUDENT
            )
        
        self.skill = Skill.objects.create(
            language='Python',
            level=SkillLevel.INTERMEDIATE
        )

        self.student_request = StudentRequest.objects.create(
            student=self.student,
            skill=self.skill,
            duration=time(hour=1),
            first_term=Term.SEPTEMBER_CHRISTMAS,
            frequency=Frequency.WEEKLY
        )

        self.tutor = User.objects.create(
            username='@tutorusername1',
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            password='password1234',
            user_type=UserType.TUTOR
            )
        
        self.enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            current_term=Term.JANUARY_EASTER,
            tutor=self.tutor,
            start_time=timezone.now() + timedelta(days=15),
            status='ongoing'
        )

    def test_valid_invoice_creation(self):
        issued_date = timezone.now()
        due_date = self.enrollment.start_time
        invoice = Invoice.objects.create(
            enrollment = self.enrollment,
            amount = 600.00,
            issued_date = issued_date,
            payment_status = 'unpaid',
            due_date = due_date
        )
    
        self.assertEqual(invoice.enrollment, self.enrollment)
        self.assertEqual(invoice.amount, 600.00)
        self.assertEqual(invoice.payment_status, 'unpaid')
        self.assertEqual(invoice.due_date, due_date)
        self.assertEqual(invoice.issued_date, issued_date)
    
    def test_due_date_cannot_be_before_issued_date(self):
        issued_date = timezone.now() + timedelta(days=15)
        due_date = timezone.now()
        with self.assertRaises(ValidationError):
            invoice = Invoice(
                enrollment = self.enrollment,
                amount = 600.00,
                issued_date = issued_date,
                payment_status = 'unpaid',
                due_date = due_date
            )
            invoice.full_clean() 

    def test_unique_invoice_for_each_enrollment(self):
        issued_date = timezone.now()
        due_date = timezone.now() + timedelta(days=15)
        Invoice.objects.create(
            enrollment = self.enrollment,
            amount = 600.00,
            issued_date = issued_date,
            payment_status = 'unpaid',
            due_date = due_date
        )
        with self.assertRaises(ValidationError):
            Invoice.objects.create(
                enrollment = self.enrollment,
                amount = 700.00,
                issued_date = issued_date,
                payment_status = 'unpaid',
                due_date = due_date
            )
