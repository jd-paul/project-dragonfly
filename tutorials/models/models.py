from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar

class UserType(models.TextChoices):
    TUTOR = 'Tutor', 'Tutor'
    ADMIN = 'Admin', 'Admin'
    STUDENT = 'Student', 'Student'

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must start with @ followed by at least three alphanumeric characters (letters, numbers, or underscore).'
        )],
        help_text='Enter a username starting with "@" followed by at least three alphanumeric characters.',
    )

    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)

    # Add a field for user type
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.STUDENT,  # Set a default user type
        help_text='Select the type of user.'
    )

    class Meta:
        """Model options."""
        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""
        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""
        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        return self.gravatar(size=60)


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class SkillLevel(models.TextChoices):
    BEGINNER = 'Beginner', 'Beginner'
    INTERMEDIATE = 'Intermediate', 'Intermediate'
    ADVANCED = 'Advanced', 'Advanced'


class Skill(models.Model):
    language = models.CharField(max_length=150, blank=False)
    level = models.CharField(max_length=15, choices=SkillLevel.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['language', 'level'], name='unique_language_level')
        ]


class TutorSkill(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='tutors')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tutor', 'skill'], name='unique_tutor_skill')
        ]


class Term(models.TextChoices):
    SEPTEMBER_CHRISTMAS = 'September-Christmas', 'September-Christmas'
    JANUARY_EASTER = 'January-Easter', 'January-Easter'
    MAY_JULY = 'May-July', 'May-July'


class Frequency(models.TextChoices):
    WEEKLY = 'weekly'
    BI_WEEKLY = 'bi-weekly'
    TWO_DAYS = '2 per week'
    THREE_DAYS = '3 per week'
    FOUR_DAYS = '4 per week'
    FIVE_DAYS = '5 per week'
    SIX_DAYS = '6 per week'
    SEVEN_DAYS = '7 per week'


class Day(models.Model):
    day_name = models.CharField(max_length=20)


class StudentRequest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='requests')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='requests')
    duration = models.TimeField()
    term = models.CharField(max_length=60, choices=Term.choices)
    frequency = models.CharField(max_length=20, choices=Frequency.choices)

class Enrollment(models.Model):
    approved_request = models.ForeignKey(StudentRequest, on_delete=models.CASCADE, related_name='enrollments')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='enrollments')
    start_time = models.DateTimeField()
    status = models.CharField(max_length=50, choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')])


class EnrollmentDays(models.Model):
    day_name =  models.ForeignKey(Day, on_delete=models.CASCADE, related_name='enrollments')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='days')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['day_name', 'enrollment'], name='unique_day_enrollment')
        ]

class Invoice(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='invoice')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateTimeField()
    payment_status = models.CharField(max_length=50, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')])
    due_date = models.DateTimeField()

# add created and modified date to every table

