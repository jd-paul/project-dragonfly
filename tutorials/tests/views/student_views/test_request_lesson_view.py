from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from tutorials.models import User, Skill, StudentRequest


class RequestLessonViewTestCase(TestCase):
   """Test students submitting requests"""
   fixtures = ['tutorials/tests/fixtures/other_users.json']


   def setUp(self):
       self.student = User.objects.get(username='@studentuser')
       self.non_student = User.objects.get(username='@tutoruser')
       self.client.login(username='@studentuser', password='Password123')


       self.skill = Skill.objects.create(language='Ruby', level='Advanced')
       self.url = reverse('student_request_form', args=[self.skill.id])


   def test_request_lesson_get_by_student(self):
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/student_request_form.html')
       self.assertIn('form', response.context)
       self.assertIn('skill', response.context)
       self.assertEqual(response.context['skill'], self.skill)


   def test_request_lesson_get_by_non_student(self):
       """Non-student users should not access RequestLesson."""
       self.client.logout()
       self.client.login(username='@tutoruser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 403)


   def test_request_lesson_get_by_anonymous(self):
       """Anonymous users should not access RequestLesson."""
       self.client.logout()
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 302)


   def test_request_non_existent_lesson(self):
       invalid_url = reverse('student_request_form', args=[99999])
       response = self.client.get(invalid_url)
       self.assertEqual(response.status_code, 404)


   def test_request_lesson_valid_post(self):


       response = self.client.post(self.url, {
           'duration': 90,
            'first_term': 'May-July',
            'frequency': 'weekly',
            'status': 'pending'
        }, follow=True)
      
       self.assertRedirects(response, reverse('your_requests'))
      
       new_request = StudentRequest.objects.get(student=self.student, skill=self.skill)
       self.assertEqual(new_request.duration, 90)
       self.assertEqual(new_request.first_term, 'May-July')
       self.assertEqual(new_request.frequency, 'weekly')
     


   def test_request_lesson_invalid_term_post(self):
       response = self.client.post(self.url, {
           'duration': 90,
            'first_term': 'May-September', # this term does not exist
            'frequency': 'weekly',
            'status': 'pending'
        }, follow=True)
      
       # No redirection
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/student_request_form.html')
       # No new request created
       self.assertFalse(StudentRequest.objects.filter(student=self.student, skill=self.skill).exists())


   def test_request_lesson_invalid_duration_post(self):
       response = self.client.post(self.url, {
           'duration': -90,
            'first_term': 'May-July',
            'frequency': 'weekly',
            'status': 'pending'
        }, follow=True)
      
       # No redirection
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/student_request_form.html')
       # No new request created
       self.assertFalse(StudentRequest.objects.filter(student=self.student, skill=self.skill).exists())


   def test_request_lesson_invalid_frequency_post(self):
       response = self.client.post(self.url, {
           'duration': 90,
            'first_term': 'May-July',
            'frequency': 'invalid_frequency',
            'status': 'pending'
        }, follow=True)
      
       # No redirection
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/student_request_form.html')
       # No new request created
       self.assertFalse(StudentRequest.objects.filter(student=self.student, skill=self.skill).exists())




   def test_request_lesson_does_not_allow_duplicate_requests(self):
       StudentRequest.objects.create(
           student=self.student,
           skill=self.skill,
           duration=90,
           first_term='May-July',
           frequency='weekly'
       )


       response = self.client.post(self.url, {
           'duration': 70,
            'first_term': 'September-Christmas',
            'frequency': 'bi-weekly',
            'status': 'pending'
        }, follow=True)


       self.assertRedirects(response, reverse('your_requests'))
       messages_list = list(get_messages(response.wsgi_request))
       self.assertIn('You have already requested this course.', str(messages_list[0]))
       # Second request not created
       self.assertFalse(StudentRequest.objects.filter(student=self.student, skill=self.skill, duration=70).exists())