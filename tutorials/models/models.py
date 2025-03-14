from decimal import Decimal
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from libgravatar import Gravatar
from django.core.exceptions import ValidationError

class UserType(models.TextChoices):
    TUTOR = 'Tutor', 'Tutor'
    ADMIN = 'Admin', 'Admin'
    STUDENT = 'Student', 'Student'
    PENDING = 'Pending', 'Pending'

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
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True, default=timezone.now)

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


class SkillLevel(models.TextChoices):
    BEGINNER = 'Beginner', 'Beginner'
    INTERMEDIATE = 'Intermediate', 'Intermediate'
    ADVANCED = 'Advanced', 'Advanced'


class Skill(models.Model):
    language = models.CharField(max_length=150, blank=False)
    level = models.CharField(max_length=15, choices=SkillLevel.choices)

    def __str__(self):
        return f"{self.language} ({self.level})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['language', 'level'], name='unique_language_level')
        ]
        ordering = ['language']

class TutorSkill(models.Model):
    tutor =  models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skills',
        limit_choices_to={'user_type': UserType.TUTOR}
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='tutors')
    price_per_hour = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00,
        help_text='Enter the hourly price for this skill.',
    )

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

class Day(models.Model):
    day_name = models.CharField(max_length=20)

class StudentRequest(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requests',
        limit_choices_to={'user_type': UserType.STUDENT}
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='requests')
    duration = models.IntegerField()
    first_term = models.CharField(max_length=60, choices=Term.choices)
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=50,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending',
    )

class Enrollment(models.Model):
    approved_request = models.ForeignKey(StudentRequest, on_delete=models.CASCADE, related_name='enrollments')
    current_term = models.CharField(max_length=60, choices=Term.choices)
    tutor =models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'user_type': UserType.TUTOR}
    )
    week_count = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(13)])
    start_time = models.DateTimeField()
    status = models.CharField(max_length=50, choices=[('ongoing', 'Ongoing'), ('ended', 'Ended'), ('cancelled', 'Cancelled')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now=True)


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


    @property
    def subtotal(self):
        try:
            week_count = self.enrollment.week_count
            frequency = self.enrollment.approved_request.frequency
            duration = self.enrollment.approved_request.duration
            tutor_skill = self.enrollment.tutor.skills.get(skill=self.enrollment.approved_request.skill)
            price_per_hour = tutor_skill.price_per_hour
            frequency_map = {
                Frequency.WEEKLY: 1,
                Frequency.BI_WEEKLY: 0.5,
            }
            return Decimal(week_count) * Decimal(frequency_map.get(frequency)) * Decimal(duration/Decimal('60')) * Decimal(price_per_hour)
        except (Enrollment.DoesNotExist, StudentRequest.DoesNotExist, TutorSkill.DoesNotExist) as e:
            # Handle exceptions
            return Decimal('0.00')
    
    def clean(self):
        super().clean()
        if(self.issued_date >= self.due_date):
            raise ValidationError({'due_date': 'Due date should be after the issued date.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class PendingTutor(models.Model):
    """Model to store pending tutor applications before admin approval."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.ManyToManyField(Skill, related_name='pending_tutors')  
    price_per_hour = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00,
        help_text='Enter the hourly price for this skill.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Pending Tutor: {self.user.full_name()}"

class TicketStatus(models.TextChoices):
    APPROVED = 'Approved', 'Approved'
    PENDING = 'Pending', 'Pending'
    REJECTED = 'Rejected', 'Rejected'

class Ticket(models.Model):
    """Model to represent tickets for issues/requests raised by students or tutors."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='modification_requests')
    ticket_type = models.CharField(
        max_length=20,
        choices=[('cancellation', 'Cancellation'), ('change', 'Change')],
        default='cancellation',
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket submitted by {self.user} - {self.ticket_type}"

    class Meta:
        """Ticket options."""
        ordering = ['-created_at']
