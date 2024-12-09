from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import (
   User
)


class ManageStudentsViewTestCase(TestCase):
   """Test ManageStudents."""


   fixtures = ['tutorials/tests/fixtures/other_users.json']
  
   def setUp(self):
       self.admin = User.objects.get(username='@adminuser')
       self.student = User.objects.get(username='@studentuser')
       self.tutor = User.objects.get(username='@tutoruser')


       self.url = reverse('manage_students')


   def test_manage_students_get_by_admin(self):
       self.client.login(username='@adminuser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'admin/manage_students.html')
       students = response.context['students']
       self.assertIn(self.student, students)


   def test_manage_students_get_by_non_admin(self):
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 403)


   def test_manage_students_get_by_anonymous(self):
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 302)