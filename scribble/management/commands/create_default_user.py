from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a default user if none exists'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.exists():
            user = User.objects.create_user(
                username='default_user',
                email='default@example.com',
                password='defaultpassword123',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created default user'))
        else:
            self.stdout.write('A user already exists')
