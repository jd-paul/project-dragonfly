from django.core.management.base import BaseCommand
from tutorials.models import (
    User, Skill, TutorSkill, Day, StudentRequest,
    Enrollment, EnrollmentDays, Invoice
)

class Command(BaseCommand):
    """Build automation command to unseed the database."""
    help = "Unseed database by deleting all records in the correct order"

    def handle(self, *args, **options):
        # Delete records in reverse dependency order
        models_to_delete = [
            Invoice,          # FK to Enrollment
            EnrollmentDays,   # FK to Enrollment
            Enrollment,       # FK to StudentRequest and Tutor
            StudentRequest,   # FK to Student and Skill
            TutorSkill,       # FK to Tutor and Skill
            Skill,            # No FK dependencies
            Day,              # No FK dependencies
            User,             # Base User model
        ]

        for model in models_to_delete:
            model_name = model.__name__
            try:
                deleted_count, _ = model.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} records from {model_name}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error deleting from {model_name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("Unseeding completed successfully."))
