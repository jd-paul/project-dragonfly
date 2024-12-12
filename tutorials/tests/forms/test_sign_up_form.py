from django.test import TestCase
from tutorials.forms import TutorSignUpForm
from tutorials.models import User, Skill, PendingTutor, UserType, SkillLevel
"""Unit tests of the sign up form."""
from django.contrib.auth.hashers import check_password
from django import forms
from django.test import TestCase
from tutorials.forms import SignUpForm
from tutorials.models import User

class SignUpFormTestCase(TestCase):
    """Unit tests of the sign up form."""

    def setUp(self):
        self.form_input = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': '@janedoe',
            'email': 'janedoe@example.org',
            'new_password': 'Password123',
            'password_confirmation': 'Password123'
        }

    def test_valid_sign_up_form(self):
        form = SignUpForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = SignUpForm()
        self.assertIn('first_name', form.fields)
        self.assertIn('last_name', form.fields)
        self.assertIn('username', form.fields)
        self.assertIn('email', form.fields)
        email_field = form.fields['email']
        self.assertTrue(isinstance(email_field, forms.EmailField))
        self.assertIn('new_password', form.fields)
        new_password_widget = form.fields['new_password'].widget
        self.assertTrue(isinstance(new_password_widget, forms.PasswordInput))
        self.assertIn('password_confirmation', form.fields)
        password_confirmation_widget = form.fields['password_confirmation'].widget
        self.assertTrue(isinstance(password_confirmation_widget, forms.PasswordInput))

    def test_form_uses_model_validation(self):
        self.form_input['username'] = 'badusername'
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_uppercase_character(self):
        self.form_input['new_password'] = 'password123'
        self.form_input['password_confirmation'] = 'password123'
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_lowercase_character(self):
        self.form_input['new_password'] = 'PASSWORD123'
        self.form_input['password_confirmation'] = 'PASSWORD123'
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_number(self):
        self.form_input['new_password'] = 'PasswordABC'
        self.form_input['password_confirmation'] = 'PasswordABC'
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_new_password_and_password_confirmation_are_identical(self):
        self.form_input['password_confirmation'] = 'WrongPassword123'
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_must_save_correctly(self):
        form = SignUpForm(data=self.form_input)
        before_count = User.objects.count()
        form.save()
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count+1)
        user = User.objects.get(username='@janedoe')
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'janedoe@example.org')
        is_password_correct = check_password('Password123', user.password)
        self.assertTrue(is_password_correct)

        
class TutorSignUpFormTest(TestCase):

    def setUp(self):
        """Setup any necessary objects for tests."""
        self.valid_data = {
            'username': '@test_tutor',  # Updated to include '@'
            'first_name': 'Test',
            'last_name': 'Tutor',
            'email': 'test.tutor@example.com',
            'skills_input': 'Python:Intermediate, Java:Advanced',
            'price_per_hour': 25.00
        }
        self.invalid_data = {
            'username': 'test_tutor',  # Invalid username without '@'
            'first_name': 'Test',
            'last_name': 'Tutor',
            'email': 'test.tutor@example.com',
            'skills_input': 'Python:Expert, InvalidSkill:InvalidLevel',
            'price_per_hour': -10.00
        }

    def test_valid_form(self):
        """Test that the form is valid with correct data."""
        form = TutorSignUpForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), "Form should be valid with correct data.")

    def test_invalid_skill_level(self):
        """Test invalid skill level."""
        form = TutorSignUpForm(data=self.invalid_data)
        self.assertFalse(form.is_valid(), "Form should be invalid with incorrect skill levels.")
        self.assertIn('skills_input', form.errors, "Error should be associated with 'skills_input' field.")

    def test_negative_price(self):
        """Test that negative price raises validation error."""
        data = self.valid_data.copy()
        data['price_per_hour'] = -5.00
        form = TutorSignUpForm(data=data)
        self.assertFalse(form.is_valid(), "Form should be invalid with negative price.")
        self.assertIn('price_per_hour', form.errors, "Error should be associated with 'price_per_hour' field.")

    def test_save_creates_user(self):
        """Test saving the form creates a user."""
        form = TutorSignUpForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), "Form should be valid before calling save.")
        user = form.save()
        self.assertEqual(user.username, self.valid_data['username'], "Saved user should have correct username.")
        self.assertEqual(user.user_type, UserType.PENDING, "User type should be set to 'PENDING'.")

    def test_save_creates_pending_tutor(self):
        """Test saving the form creates a PendingTutor."""
        form = TutorSignUpForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        pending_tutor = PendingTutor.objects.get(user=user)
        self.assertEqual(pending_tutor.price_per_hour, self.valid_data['price_per_hour'], 
                         "PendingTutor should have correct price_per_hour.")

    def test_save_creates_skills(self):
        """Test saving the form creates skills."""
        form = TutorSignUpForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        form.save()
        skills = Skill.objects.all()
        self.assertEqual(skills.count(), 2, "Two skills should be created.")
        skill_names = [skill.language for skill in skills]
        self.assertIn('Python', skill_names, "Python skill should be created.")
        self.assertIn('Java', skill_names, "Java skill should be created.")

    def test_empty_skills_input(self):
        """Test that the form is valid with empty skills_input."""
        data = self.valid_data.copy()
        data['skills_input'] = ''  # Empty skills_input
        form = TutorSignUpForm(data=data)
        self.assertTrue(form.is_valid(), "Form should be valid with empty skills_input.")
        user = form.save()
        self.assertEqual(PendingTutor.objects.get(user=user).skills.count(), 0, "No skills should be added.")

    def test_min_price_per_hour(self):
        """Test that the form is valid with a price of 0.00."""
        data = self.valid_data.copy()
        data['price_per_hour'] = 0.00
        form = TutorSignUpForm(data=data)
        self.assertTrue(form.is_valid(), "Form should be valid with minimum price_per_hour.")
        
    def test_invalid_email_format(self):
        """Test invalid email format."""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email-format'
        form = TutorSignUpForm(data=data)
        self.assertFalse(form.is_valid(), "Form should be invalid with incorrect email format.")
        self.assertIn('email', form.errors, "Error should be associated with 'email' field.")

    def test_duplicate_username(self):
        """Test duplicate username validation."""
        User.objects.create(username='@test_tutor', email='existing@example.com')  # Updated to have '@'
        form = TutorSignUpForm(data=self.valid_data)
        self.assertFalse(form.is_valid(), "Form should be invalid with duplicate username.")
        self.assertIn('username', form.errors, "Error should be associated with 'username' field.")
