from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.messages import get_messages
from tutorials.models import UserType, Skill, StudentRequest, Enrollment

class SkillListViewTestCase(TestCase):

    fixtures = [
        'tutorials/tests/fixtures/default_user.json',
        'tutorials/tests/fixtures/other_users.json'
    ]

    