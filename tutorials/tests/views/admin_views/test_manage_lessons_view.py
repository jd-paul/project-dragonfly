from django.test import TestCase
from django.urls import reverse
from tutorials.models import User, Enrollment, Skill, StudentRequest
from django.utils.timezone import localtime
import random
import string
from django.core.management import call_command
from tutorials.models import User, UserType, Frequency, Term

def generate_unique_username():
    """Generate a unique username to avoid conflicts."""
    return '@' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def generate_unique_email():
    """Generate a unique email to avoid conflicts."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '@example.com'


# Fixed time for all tests
fixed_time = localtime()


class ManageLessonsViewTestCase(TestCase):
    def setUp(self):

        random.seed(51005)

        # Generate unique usernames and emails
        admin_username = generate_unique_username()
        student_username = generate_unique_username()
        tutor_username = generate_unique_username()
        admin_email = generate_unique_email()
        tutor_email = generate_unique_email()
        student_email = generate_unique_email()

        # Create admin, tutor and student users with unique usernames and emails
        self.admin_user = User.objects.create_user(
            username=admin_username,
            password='admin_password123',
            email=admin_email,
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN,
        )

        self.tutor_user = User.objects.create_user(
            username=tutor_username,
            password='tutor_password123',
            email=tutor_email,
            first_name='tutor',
            last_name='User',
            user_type=UserType.TUTOR
        )

        self.student_user = User.objects.create_user(
            username=student_username,
            password='student_password123',
            email=student_email,
            first_name='Student',
            last_name='User',
            user_type=UserType.STUDENT
        )

        # URL 
        self.url = reverse('manage_lessons')

        # Skill 
        self.skill = Skill.objects.create(language=f'Lang{3}', level='Beginner')
        
        # StudentRequest
        self.student_request = StudentRequest.objects.create(
            student=self.student_user,
            skill=self.skill,
            duration=10,  # Ensure a value for the duration
            first_term= Term.JANUARY_EASTER,
            frequency= Frequency.WEEKLY
        )

        # Enrollments
        self.ongoing_enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            tutor=self.tutor_user,
            current_term=self.student_request.first_term,
            week_count=10,
            start_time=fixed_time,
            status='ongoing'
        )
        self.ended_enrollment = Enrollment.objects.create(
            approved_request=self.student_request,
            tutor=self.tutor_user,
            current_term=self.student_request.first_term,
            week_count=8,
            start_time=fixed_time,
            status='ended'
        )

        # URL
        self.url = reverse('manage_lessons')

    def test_manage_lessons_get_by_admin(self):
        """Test that an admin user can access the ManageLessons view."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/manage_lessons.html')
        self.assertIn('lessons', response.context)

    def test_manage_lessons_get_by_non_admin(self):
        """Test that a non-admin user cannot access the ManageLessons view."""
        self.client.login(username=self.tutor_user.username, password='tutor_password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_manage_lessons_get_by_anonymous_user(self):
        """Test that an anonymous user cannot access the ManageLessons view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_manage_lessons_search_filter(self):
        """Test filtering lessons by student name."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        response = self.client.get(self.url, {'search': self.student_user.first_name})
        self.assertEqual(response.status_code, 200)
        lessons = response.context['lessons']
        self.assertIn(self.ongoing_enrollment, lessons)
        self.assertIn(self.ended_enrollment, lessons)

    def test_manage_lessons_status_filter(self):
        """Test filtering lessons by status."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        response = self.client.get(self.url, {'status': 'ongoing'})
        self.assertEqual(response.status_code, 200)
        lessons = response.context['lessons']
        self.assertIn(self.ongoing_enrollment, lessons)
        self.assertNotIn(self.ended_enrollment, lessons)

    def test_manage_lessons_pagination(self):
        """Test pagination for lessons."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        # Create more enrollments to test pagination
        for _ in range(15):
            Enrollment.objects.create(
                approved_request=self.student_request,
                tutor=self.tutor_user,
                current_term=self.student_request.first_term,
                week_count=4,
                start_time=fixed_time,
                status='ongoing'
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        lessons = response.context['lessons']
        self.assertTrue(lessons.paginator.num_pages > 1)

    def test_manage_lessons_post_end_lesson(self):
        """Test ending a lesson by admin."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        response = self.client.post(self.url, {
            'lesson_id': self.ongoing_enrollment.id,
            'action': 'end'
        })
        self.assertRedirects(response, self.url)

        # Verify that the lesson status has been updated
        self.ongoing_enrollment.refresh_from_db()
        self.assertEqual(self.ongoing_enrollment.status, 'ended')

    def test_manage_lessons_search_non_existent_student(self):
        """Test searching for a non-existent student."""
        self.client.login(username=self.admin_user.username, password='admin_password123')
        
        # Search
        non_existent_student_name = "NonExistentName-POSER"
        response = self.client.get(self.url, {'search': non_existent_student_name})
        self.assertEqual(response.status_code, 200)
        
        lessons = response.context['lessons']
        
        # Verify that the lessons object list is empty
        self.assertEqual(len(lessons.object_list), 0)  
        self.assertEqual(lessons.paginator.count, 0)

