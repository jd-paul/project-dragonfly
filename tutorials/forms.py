"""Forms for the tutorials app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, Skill, TutorSkill, UserType, StudentRequest, PendingTutor, Ticket, TicketStatus, Enrollment
from django.core.exceptions import ValidationError
from .models import StudentRequest, Skill, SkillLevel

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class UserForm(forms.ModelForm):
    """Form to update user profiles."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        return user
    
class TutorSignUpForm(forms.ModelForm):
    skills_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Language:Level, e.g., Python:Intermediate, Java:Advanced'}),
        label="Skills (Language:Level)"
    )
    price_per_hour = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        label="Price per hour",
        min_value=0.00,
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_skills_input(self):
        skills_input = self.cleaned_data['skills_input']
        skills = skills_input.split(',')
        for skill in skills:
            skill = skill.strip()
            if ':' in skill:
                _, level = skill.split(':', 1)
                if level.strip() not in SkillLevel.values:
                    raise ValidationError(f"Invalid skill level: {level.strip()}")
        return skills_input

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = UserType.PENDING
        if commit:
            user.save()

        skills = self.cleaned_data['skills_input'].split(',')
        price_per_hour = self.cleaned_data['price_per_hour']
        
        pending_tutor = PendingTutor.objects.create(user=user, price_per_hour=price_per_hour)
        
        for skill_name in skills:
            skill_name = skill_name.strip()
            if skill_name:
                if ':' in skill_name:
                    language, level = skill_name.split(':', 1)
                else:
                    language, level = skill_name, SkillLevel.BEGINNER
                skill, created = Skill.objects.get_or_create(language=language.strip(), level=level.strip())
                pending_tutor.skills.add(skill)

        return user




class StudentRequestForm(forms.ModelForm):
    class Meta:
        model = StudentRequest
        exclude = ['student', 'skill', 'status']
        widgets = {
            'duration': forms.NumberInput(attrs={'min': 10}),
            'first_term': forms.Select(),
            'frequency': forms.Select(),
        }
        labels = {
            'duration': '(in minutes)',
        }
        help_texts = {
            'duration': 'Please enter the duration in minutes e.g. 75',
        }
        
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration is not None and duration < 10:
            raise ValidationError("Duration must be at least 10 minutes.")
        return duration


class TicketForm(forms.ModelForm):
    """Form for submitting and updating tickets."""
  
    class Meta:
        model = Ticket
        fields = ['ticket_type', 'description', 'enrollment']  # Include enrollment field explicitly
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'description': 'Please explain in detail your desired modification.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            # Ensure enrollment is set in the case of new tickets (if enrollment is not provided, it should raise an error)
            self.fields['enrollment'].required = True

    def clean_enrollment(self):
        enrollment = self.cleaned_data.get('enrollment')
        if enrollment and not Enrollment.objects.filter(id=enrollment.id).exists():
            raise forms.ValidationError('Invalid enrollment.')
        return enrollment
