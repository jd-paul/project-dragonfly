from datetime import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from tutorials.models import User, Skill, TutorSkill, Enrollment, StudentRequest


class YourRequestsViewAndDeleteTestCase(TestCase):
   """Test students viewing their requests"""


   fixtures = ['tutorials/tests/fixtures/other_users.json']


   def setUp(self):
       self.student = User.objects.get(username='@studentuser')
       self.non_student = User.objects.get(username='@tutoruser')
       self.client.login(username='@studentuser', password='Password123')


       self.skill_ruby = Skill.objects.create(language='Ruby', level='Beginner')
       self.skill_scala = Skill.objects.create(language='Scala', level='Advanced')
       self.skill_java = Skill.objects.create(language='Java', level='Advanced')




       self.approved_request = StudentRequest.objects.create(
           student=self.student,
           skill=self.skill_ruby,
           duration=30,
           first_term='September-Christmas',
           frequency='weekly',
           status='approved'
       )


       self.rejected_request = StudentRequest.objects.create(
           student=self.student,
           skill=self.skill_scala,
           duration=90,
           first_term='May-July',
           frequency='weekly',
           status='rejected'
       )


       self.pending_request = StudentRequest.objects.create(
           student=self.student,
           skill=self.skill_java,
           duration=90,
           first_term='May-July',
           frequency='bi-weekly',
           status='pending'
       )


       self.url = reverse('your_requests')


   def test_your_requests_get_by_student(self):
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/your_requests.html')
       self.assertIn('student_requests', response.context)
       self.assertIn(self.approved_request, response.context['student_requests'])


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


   def test_can_not_delete_approved_request(self):
       pass
