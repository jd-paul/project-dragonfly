from django.urls import reverse
from django.test import TestCase
from tutorials.models import User
from tutorials.forms import TutorSignUpForm

class TutorSignUpViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('tutor_signup')

    def test_tutor_sign_up_get(self):
        # Test GET request for sign-up form
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor_sign_up.html')

    def test_tutor_sign_up_logged_in_user(self):
        # Test that a logged-in user is redirected to the dashboard
        user = User.objects.create_user(username='student', email='student@domain.com', password='password123')
        self.client.login(username='student', password='password123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))  # Assuming 'dashboard' is the correct redirect URL

    def test_tutor_sign_up_post_valid(self):
        # Test POST request with valid data
        response = self.client.post(self.url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'username': '@testuser',  # Valid username
            'password1': 'password123',
            'password2': 'password123',
            'price_per_hour': 20.00,
            'skills_input': 'Python, Django',
        })
        self.assertRedirects(response, reverse('tutor_application_success'))

    def test_tutor_sign_up_post_invalid(self):
        # Test POST request with missing email
        response = self.client.post(self.url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': '@invaliduser',
            'password1': 'password123',
            'password2': 'password123',
            'price_per_hour': 20.00,
            'skills_input': 'Python, Django',
        })
        # Access the form from the response context
        form = response.context.get('form')
        self.assertTrue(form.errors)
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'], ['This field is required.'])

    def test_tutor_sign_up_post_invalid_username(self):
        # Test POST request with invalid username (should start with '@')
        response = self.client.post(self.url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'username': 'invaliduser',  # Invalid username without '@'
            'password1': 'password123',
            'password2': 'password123',
            'price_per_hour': 20.00,
            'skills_input': 'Python, Django',
        })
        # Access the form from the response context
        form = response.context.get('form')
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ['Username must start with @ followed by at least three alphanumeric characters (letters, numbers, or underscore).'])

    def test_tutor_sign_up_post_missing_data(self):
        # Test missing required data in the POST request
        response = self.client.post(self.url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'username': '@testuser',
            'password1': 'password123',
            'password2': 'password123',
        })
        
        # Access the form from the response context
        form = response.context.get('form')
        
        # Assert that there are form errors (since some fields are missing)
        self.assertTrue(form.errors)
        
        # Assert that 'skills_input' is not in the errors (since it's not required)
        self.assertNotIn('skills_input', form.errors)
        
        # Assert that the 'price_per_hour' field has the correct error
        self.assertIn('price_per_hour', form.errors)
        self.assertEqual(form.errors['price_per_hour'], ['This field is required.'])
