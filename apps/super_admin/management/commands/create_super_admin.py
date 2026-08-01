"""
Management command: python manage.py create_super_admin
Creates the first Super Admin account interactively.
Never exposed via HTTP — CLI only.
"""
import hashlib
import secrets
import getpass
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a Super Admin account (CLI only)'

    def handle(self, *args, **options):
        from apps.super_admin.models import SuperAdminUser

        self.stdout.write('\n=== DADCARE Super Admin Setup ===\n')
        email = input('Email: ').strip().lower()
        full_name = input('Full name: ').strip()
        password = getpass.getpass('Password (min 12 chars): ')

        if len(password) < 12:
            self.stderr.write('Password must be at least 12 characters.')
            return

        if SuperAdminUser.objects.filter(email=email).exists():
            self.stderr.write(f'Super Admin with email {email} already exists.')
            return

        salt = secrets.token_hex(16)
        pw_hash = f"{salt}:{hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()}"

        admin = SuperAdminUser.objects.create(
            email=email,
            full_name=full_name,
            password_hash=pw_hash,
            totp_enabled=False,
        )

        self.stdout.write(self.style.SUCCESS(f'\nSuper Admin created: {email}'))
        self.stdout.write('1. Login: control.dadcare.app/sa/auth/login/')
        self.stdout.write('2. Setup TOTP: /sa/auth/setup-totp/')
        self.stdout.write('3. Confirm TOTP: /sa/auth/confirm-totp/')
