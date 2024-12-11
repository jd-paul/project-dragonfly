from django.test import TestCase
from django.core.exceptions import PermissionDenied
from tutorials.models import User
from tutorials.views import is_admin, is_student, is_tutor


class HelperFunctionsTestCase(TestCase):
   """Test is_admin and is_student helper functions."""


   fixtures = ['tutorials/tests/fixtures/other_users.json']
  
   def setUp(self):
       self.admin = User.objects.get(username='@adminuser')
       self.student = User.objects.get(username='@studentuser')
       self.tutor = User.objects.get(username='@tutoruser')


   def test_is_admin_with_admin_user(self):
       self.assertTrue(is_admin(self.admin))


   def test_is_admin_with_non_admin_raises(self):
       with self.assertRaises(PermissionDenied):
           is_admin(self.student)
       with self.assertRaises(PermissionDenied):
           is_admin(self.tutor)


   def test_is_student_with_student_user(self):
       self.assertTrue(is_student(self.student))


   def test_is_student_with_non_student_raises(self):
       with self.assertRaises(PermissionDenied):
           is_student(self.admin)
       with self.assertRaises(PermissionDenied):
           is_student(self.tutor)

    
   def test_is_tutor_with_tutor_user(self):
       self.assertTrue(is_tutor(self.tutor))


   def test_is_tutor_with_non_tutor_raises(self):
       with self.assertRaises(PermissionDenied):
           is_tutor(self.admin)
       with self.assertRaises(PermissionDenied):
           is_tutor(self.student)