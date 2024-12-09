from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models import Skill, SkillLevel, UserType, PendingTutor
from tutorials.forms import TutorSignUpForm

User = get_user_model()

class TutorSignUpViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # URL for the tutor sign-up view
        cls.url = reverse('tutor_sign_up')

        # Create a test skill for the tutor sign-up
        cls.skill = Skill.objects.create(language="Python", level=SkillLevel.INTERMEDIATE)

    def setUp(self):
        # Create a client for each test
        self.client = Client()

    def test_tutor_sign_up_get(self):
        """Test GET request to display the tutor sign-up form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor_sign_up.html')

        # Check that the form is present in the context
        form = response.context['form']
        self.assertIsInstance(form, TutorSignUpForm)

    def test_tutor_sign_up_post_valid(self):
        """Test POST request with valid data to sign up as a tutor."""
        data = {
            'username': 'newtutor',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'newtutor@example.com',
            'skills_input': 'Python:Intermediate',
            'price_per_hour': 25.00,
        }

        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('tutor_application_success'))

        # Verify the user is created
        user = User.objects.get(username='newtutor')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'newtutor@example.com')

        # Verify the pending tutor is created
        pending_tutor = PendingTutor.objects.get(user=user)
        self.assertEqual(pending_tutor.price_per_hour, 25.00)

        # Verify the skill is assigned to the tutor
        self.assertTrue(pending_tutor.skills.filter(language='Python').exists())

    def test_tutor_sign_up_post_invalid(self):
        """Test POST request with invalid data."""
        # Missing required field `email`
        data = {
            'username': 'invalidtutor',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'skills_input': 'Python:Intermediate',
            'price_per_hour': 25.00,
        }

        response = self.client.post(self.url, data)

        # The form should be invalid and return to the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor_sign_up.html')
        
        # Verify form errors
        self.assertFormError(response, 'form', 'email', 'This field is required.')

    def test_tutor_sign_up_post_missing_data(self):
        """Test POST request with missing data for required fields."""
        # Missing `skills_input` and `price_per_hour`
        data = {
            'username': 'missingdata',
            'first_name': 'Noah',
            'last_name': 'Taylor',
            'email': 'missingdata@example.com',
        }

        response = self.client.post(self.url, data)

        # The form should be invalid and return to the same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tutor_sign_up.html')

        # Verify form errors
        self.assertFormError(response, 'form', 'skills_input', 'This field is required.')
        self.assertFormError(response, 'form', 'price_per_hour', 'This field is required.')

    def test_tutor_sign_up_redirect_on_success(self):
        """Test that after a valid form submission, the user is redirected to success page."""
        data = {
            'username': 'validtutor',
            'first_name': 'Lucas',
            'last_name': 'Brown',
            'email': 'validtutor@example.com',
            'skills_input': 'Python:Advanced, Java:Intermediate',
            'price_per_hour': 40.00,
        }

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse('tutor_application_success'))

    def test_tutor_sign_up_logged_in_user(self):
        """Test that a logged-in user is prevented from accessing the sign-up view."""
        # Simulate a logged-in user
        user = User.objects.create_user(username='existinguser', email='existinguser@example.com', password='password123')
        self.client.login(username='existinguser', password='password123')

        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('home'))  # Assuming redirect goes to home page
        self.assertEqual(response.status_code, 302)
