from datetime import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from tutorials.models import User, UserType, Skill, TutorSkill, Enrollment, StudentRequest


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
       self.delete_approved_url = reverse('delete_your_request', args=[self.approved_request.id])
       self.delete_rejected_url = reverse('delete_your_request', args=[self.rejected_request.id])
       self.delete_pending_url = reverse('delete_your_request', args=[self.pending_request.id])


    def test_your_requests_get_by_student(self):
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/your_requests.html')
       self.assertIn('student_requests', response.context)
       self.assertIn(self.approved_request, response.context['student_requests'])
       self.assertIn(self.rejected_request, response.context['student_requests'])
       self.assertIn(self.pending_request, response.context['student_requests'])


    def test_your_requests_get_by_non_student(self):
       """Non-student users should not access YourRequests."""
       self.client.logout()
       self.client.login(username='@tutoruser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 403)


    def test_your_requests_get_by_anonymous(self):
       """Anonymous users should not access YourRequests."""
       self.client.logout()
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 302)


    def test_can_delete_pending_request(self):
        """Test student can delete pending request"""
        response = self.client.post(self.delete_pending_url, follow=True)
        self.assertRedirects(response, reverse('your_requests'))
        self.assertFalse(StudentRequest.objects.filter(id=self.pending_request.id).exists())

    def test_cannot_delete_rejected_request(self):
        """Test student cannot delete rejected request"""
        response = self.client.post(self.delete_rejected_url, follow=True)
        self.assertRedirects(response, reverse('your_requests'))
        self.assertTrue(StudentRequest.objects.filter(id=self.rejected_request.id).exists())
        messages_list = list(get_messages(response.wsgi_request))
        self.assertIn('You cannot delete this request.', str(messages_list[0]))

    def test_cannot_delete_approved_request(self):
        """Test student cannot delete rejected request"""
        response = self.client.post(self.delete_approved_url, follow=True)
        self.assertRedirects(response, reverse('your_requests'))
        self.assertTrue(StudentRequest.objects.filter(id=self.approved_request.id).exists())
        messages_list = list(get_messages(response.wsgi_request))
        self.assertIn('You cannot delete this request.', str(messages_list[0]))

    def test_delete_request_invalid_id(self):
        response = self.client.post(reverse('delete_your_request', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_another_students_request(self):
        # Create another student user and request
        other_student = User.objects.get(username='@peterpickles')
        other_req = StudentRequest.objects.create(
            student=other_student,
            skill=self.skill_scala,
            duration=50,
            first_term='May-July',
            frequency='weekly',
            status='pending'
        )
        response = self.client.post(reverse('delete_your_request', args=[other_req.id]))
        self.assertEqual(response.status_code, 404)

        