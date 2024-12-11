from django.core.management.base import BaseCommand
from tutorials.models import (
    User, UserType, Skill, SkillLevel, TutorSkill,
    StudentRequest, Term, Frequency, Enrollment,
    EnrollmentDays, Day, Invoice
)
from django.utils import timezone
from faker import Faker
from datetime import timedelta
import random
from django.db import transaction
from decimal import Decimal
from datetime import time

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@duck_admin.com', 'first_name': 'John', 'last_name': 'Doe', 'user_type': 'Admin'},
    {'username': '@janedoe', 'email': 'jane.doe@duck_tutor.com', 'first_name': 'Jane', 'last_name': 'Doe', 'user_type': 'Tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@duck_student.com', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_type': 'Student'},
]

class Command(BaseCommand):
    """Build automation command to seed the database."""
    USER_COUNT = 100
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        super().__init__()
        self.faker = Faker('en_GB')
        self.existing_emails = set()
        self.existing_usernames = set()
        self.tutors = []
        self.students = []
        self.skills = []
        
    def clear_data(self):
        """Clear existing data."""
        self.stdout.write('\nClearing existing data...')

        User.objects.all().delete()
        TutorSkill.objects.all().delete()
        StudentRequest.objects.all().delete()
        Day.objects.all().delete()
        Enrollment.objects.all().delete()
        EnrollmentDays.objects.all().delete()
        Invoice.objects.all().delete()

        self.stdout.write('\nExisting data cleared.')

    def handle(self, *args, **options):
        self.clear_data()

        self.create_users()
        self.create_skills()
        self.create_tutor_skills()
        self.create_student_requests()
        self.create_days()
        self.create_enrollments()
        self.stdout.write('\nSeeding complete.')

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

        self.tutors = list(User.objects.filter(user_type=UserType.TUTOR))
        self.students = list(User.objects.filter(user_type=UserType.STUDENT))

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)
            if data['email']:
                self.existing_emails.add(data['email'])
            if data['username']:
                self.existing_usernames.add(data['username'])

    def generate_random_users(self):
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            self.stdout.write(f"Seeding user {user_count}/{self.USER_COUNT}", ending='\r')
            self.generate_user()
            user_count = User.objects.count()
        self.stdout.write("\nUser seeding complete.")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        username = self.create_unique_username(first_name, last_name)
        user_type = self.assign_user_type()

        if (user_type == UserType.STUDENT):
            email = self.create_unique_email(first_name, last_name, "@student.com")
        elif (user_type == UserType.TUTOR):
            email = self.create_unique_email(first_name, last_name, "@tutor.com")
        elif (user_type == UserType.ADMIN):
            email = self.create_unique_email(first_name, last_name, "@admin.com")
        
        self.try_create_user({
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'user_type': user_type
        })

    def try_create_user(self, data):
        try:
            self.create_user(data)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating user {data['username']}: {str(e)}\n"))
    
    def create_user(self, data):
            # Generate a random datetime within the last 2 months
            now = timezone.now()
            created_days_ago = random.randint(0, 60)
            created_time = now - timedelta(days=created_days_ago)
            created_time = created_time.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # Generate updated_at within a range after created_at
            update_days_after = random.randint(0, 30)  # Can be updated up to 30 days after creation
            updated_time = created_time + timedelta(days=update_days_after)
            updated_time = updated_time.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            data['created_at'] = created_time
            data['updated_at'] = updated_time
            
            User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=self.DEFAULT_PASSWORD,
                first_name=data['first_name'],
                last_name=data['last_name'],
                user_type=data['user_type'],
                created_at=data['created_at'],
                updated_at=data['updated_at']
            )

    def assign_user_type(self):
        """Assign a user type with 60% chance for Student, 20% for Tutor, and 20% for Admin."""
        rand_num = random.random()  # Generates a float between 0 and 1
        if rand_num < 0.6:
            return 'Student'  # 60% chance
        elif rand_num < 0.8:
            return 'Tutor'    # 20% chance (0.6 to 0.8)
        else:
            return 'Admin'    # 20% chance (0.8 to 1.0)

    def create_unique_username(self, first_name, last_name):
        base_username = '@' + first_name.lower() + last_name.lower()
        username = base_username
        counter = 1

        while username in self.existing_usernames:
            username = f"{base_username}{counter}"
            counter += 1

        self.existing_usernames.add(username)
        return username

    def create_unique_email(self, first_name, last_name, domain='@gmail.com'):
        base_email = f"{first_name.lower()}.{last_name.lower()}{domain}"
        email = base_email
        counter = 1

        while email in self.existing_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}{domain}"
            counter += 1

        self.existing_emails.add(email)
        return email

    def create_skills(self):
        self.stdout.write('Creating skills...')

        languages = [
            'Java', 'Python', 'JavaScript', 'Scala', 'Ruby', 'Go', 'C++', 'C', 'Swift', 'Perl', 'Rust',
        ]
        levels = [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED]
        self.skills = []

        for language in languages:
            for level in levels:
                skill, created = Skill.objects.get_or_create(language=language, level=level)
                self.skills.append(skill)

                if created:
                    self.stdout.write(f'Created skill: {skill.language} ({skill.level})')
                else:
                    self.stdout.write(f'Skill already exists: {skill.language} ({skill.level})')

    def create_tutor_skills(self):
        self.stdout.write('Assigning skills to tutors...')

        if not self.tutors:
            self.stdout.write(('No tutors found to assign skills to.'))
            return

        for tutor in self.tutors:
            assigned_skills = random.sample(self.skills, k=random.randint(7, 10))  # Each tutor gets 3-5 random skills
            for skill in assigned_skills:
                tutor_skill_data = {
                    'tutor': tutor,
                    'skill': skill,
                    'price_per_hour': self.generate_hourly_price() 
                }
            
                try:
                    with transaction.atomic():
                        TutorSkill.objects.create(**tutor_skill_data)
                        self.stdout.write(f'Assigned: {skill.language} ({skill.level}) to {tutor.username}')
                    
                except Exception as e:
                        self.stdout.write(f'Could not assign {skill.language} ({skill.level}) to {tutor.username}: {e}')

    def generate_hourly_price(self):
        price = Decimal(random.uniform(20, 150)).quantize(Decimal('0.01'))
        return price

    def create_student_requests(self):
        self.stdout.write('Creating student requests...')

        # Check for required data
        if not self.students:
            self.stdout.write('No students found to assign requests to.')
            return
        
        if not self.skills:
            self.stdout.write('No skills found to assign to requests.')
            return

        # Possible values for request fields
        durations = [30, 60, 90]
        terms = [Term.SEPTEMBER_CHRISTMAS, Term.JANUARY_EASTER, Term.MAY_JULY]
        frequencies = [Frequency.WEEKLY, Frequency.BI_WEEKLY]

        # Generate student requests
        for student in self.students:
            k = min(len(self.skills), random.randint(5, 10))  # Ensure valid sampling
            requested_skills = random.sample(self.skills, k=k)

            statuses = ['pending', 'rejected', 'approved']
            
            random.shuffle(statuses)
            
            for skill in requested_skills:
                status = statuses[random.randint(0, 2)]  # Randomly choose from 'pending', 'rejected', 'approved'
                
                student_request_data = {
                    'student': student,
                    'skill': skill,
                    'duration': random.choice(durations),
                    'first_term': random.choice(terms),
                    'frequency': random.choice(frequencies),
                    'status': status,  
                }
                
                try:
                    with transaction.atomic():
                        StudentRequest.objects.create(**student_request_data)
                        self.stdout.write(f'Student: {student.username} requested: {skill.language} ({skill.level}) with status {status}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating request for {student.username}: {e}'))

    def create_days(self):
        self.stdout.write('Creating days...')

        day_names = [
            'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'
        ]

        for day_name in day_names:
                day, created = Day.objects.get_or_create(day_name=day_name)
                if created:
                    self.stdout.write(f'Created day: {day_name}')
                else:
                    self.stdout.write(f'Day already exists: {day_name}')


    def create_enrollments(self):
        self.stdout.write('Creating enrollments for approved requests...')

        approved_requests = StudentRequest.objects.filter(status='approved')
        if not approved_requests.exists():
            self.stdout.write('No approved requests found to create enrollments for.')
            return

        for req in approved_requests:
            # Find a tutor who teaches this skill
            tutor_skills = TutorSkill.objects.filter(skill=req.skill)
            if not tutor_skills.exists():
                self.stdout.write(f'No tutors found who teach {req.skill} for request {req.id}. Skipping enrollment.')
                continue

            chosen_tutor_skill = random.choice(tutor_skills)
            tutor = chosen_tutor_skill.tutor
            start_time = timezone.now() + timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            enrollment_data = {
                'approved_request': req,
                'current_term': req.first_term,
                'tutor': tutor,
                'week_count': random.randint(1,13),
                'start_time': start_time,
                'status': 'ongoing'
            }
            try:
                with transaction.atomic():
                    Enrollment.objects.create(**enrollment_data)
                    self.stdout.write(f'Created enrollment for request {req.id}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating enrollment for request {req.id}: {e}'))