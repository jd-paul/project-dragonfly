from django.core.management.base import BaseCommand
from tutorials.models import User
from django.utils import timezone
from faker import Faker
from datetime import timedelta
import random


user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@duck_admin.com', 'first_name': 'John', 'last_name': 'Doe', 'user_type': 'Admin'},
    {'username': '@janedoe', 'email': 'jane.doe@duck_tutor.com', 'first_name': 'Jane', 'last_name': 'Doe', 'user_type': 'Tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@duck_student.com', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_type': 'Student'},
]

class Command(BaseCommand):
    """Build automation command to seed the database."""
    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        super().__init__()
        self.faker = Faker('en_GB')
        self.existing_emails = set()
        self.existing_usernames = set()

    def handle(self, *args, **options):
        User.objects.all().delete()
        self.create_users()
        self.users = User.objects.all()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

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

        if (user_type == 'Student'):
            email = self.create_unique_email(first_name, last_name, "@student.com")
        elif (user_type == 'Tutor'):
            email = self.create_unique_email(first_name, last_name, "@tutor.com")
        elif (user_type == 'Admin'):
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
        """Assign a user type with 90% chance for Student, 5% for Tutor, and 5% for Admin."""
        rand_num = random.random()  # Use random.random()
        if rand_num < 0.9:
            return 'Student'  # 90% chance
        elif rand_num < 0.95:
            return 'Tutor'    # 5% chance
        else:
            return 'Admin'    # 5% chance

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