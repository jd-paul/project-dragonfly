from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models import User, Skill


class SkillListViewTestCase(TestCase):
   """Test SkillListView"""
   fixtures = ['tutorials/tests/fixtures/other_users.json']


   def setUp(self):
       self.student = User.objects.get(username='@studentuser')
       self.non_student = User.objects.get(username='@tutoruser')
      
       self.skill_ruby = Skill.objects.create(language='Ruby', level='Beginner')
       self.skill_scala = Skill.objects.create(language='Scala', level='Advanced')
       self.skill_java = Skill.objects.create(language='Java', level='Advanced')


       # create additional skills to test pagination


       for i in range(5):
           Skill.objects.create(language=f'Lang{i}', level='Beginner')
           Skill.objects.create(language=f'Lang{i}', level='Intermediate')
           Skill.objects.create(language=f'Lang{i}', level='Advanced')


       self.url = reverse('offered_skill_list')


   def test_skill_list_get_by_student(self):
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       self.assertTemplateUsed(response, 'student/offered_skill_list.html')
       self.assertIn('is_paginated', response.context)
       self.assertIn('skills', response.context)
       self.assertIn('query', response.context)
       self.assertIn('current_level', response.context)
       self.assertIn('levels', response.context)


   def test_skill_list_get_by_non_student(self):
       """Non-student users should not access SkillListView."""
       self.client.login(username='@tutoruser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 403)


   def test_skill_list_get_by_anonymous(self):
       """Anonymous users should not access SkillListView."""
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 302)


   def test_skill_list_filter_by_query(self):
       """Filter by query should give appropriate results"""
       # filter by Ruby (exists)
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url, {'q': 'Ruby'})
       self.assertEqual(response.status_code, 200)
       filtered_skills = response.context['skills']
       self.assertIn(self.skill_ruby, filtered_skills)
       self.assertNotIn(self.skill_scala, filtered_skills)
       self.assertNotIn(self.skill_java, filtered_skills)


       # filter by Go (does not exist)
       response = self.client.get(self.url, {'q': 'Go'})
       skills = response.context['skills']
       self.assertEqual(len(skills), 0)




   def test_skill_list_filter_by_level(self):
       """Filter by level should give appropriate results"""
       # filter by advanced level: there are 7 skills with this level
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url, {'level': 'Advanced'})
       self.assertEqual(response.status_code, 200)
       filtered_skills = response.context['skills']
       self.assertNotIn(self.skill_ruby, filtered_skills)
       self.assertIn(self.skill_scala, filtered_skills)
       self.assertIn(self.skill_java, filtered_skills)
       self.assertTrue(len(filtered_skills) == 7)
      


   def test_skill_list_filter_by_query_and_level(self):
       """Filter by both level and query should give appropriate results"""
       # try with Ru instead of Ruby: only one skill with these specs
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url, {'q': 'Ru','level': 'Beginner'})
       self.assertEqual(response.status_code, 200)
       filtered_skills = response.context['skills']
       self.assertIn(self.skill_ruby, filtered_skills)
       self.assertTrue(len(filtered_skills) == 1)


   def test_skill_list_paginator_first_page(self):
       """Test pagination on the first page."""
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url)
       self.assertEqual(response.status_code, 200)
       skills = response.context['skills']
       # paginate_by is 10, we have 18 skills, there should be two pages
       self.assertTrue(skills.paginator.num_pages > 1)
       # check we are on page 1
       self.assertEqual(skills.number, 1)


   def test_skill_list_paginator_other_page(self):
       """Test pagination on a page other than the first."""
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url, {'page': 2})
       self.assertEqual(response.status_code, 200)
       skills = response.context['skills']
       # check we are on page 2
       self.assertEqual(skills.number, 2)


   def test_skill_list_paginator_invalid_page(self):
       """Test pagination on a non existent page."""
       self.client.login(username='@studentuser', password='Password123')
       response = self.client.get(self.url, {'page': 99999})
       self.assertEqual(response.status_code, 200)
       skills = response.context['skills']
       # we should stay on the last existing page(2)
       self.assertEqual(skills.number, 2)




