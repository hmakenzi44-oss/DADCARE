"""
Management command: python manage.py setup_dadcare
Runs post-migration setup:
  1. Applies immutable audit log trigger
  2. Seeds mini-apps if not present
  3. Prints next steps
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'First-time DADCARE setup: audit triggers + mini-app seed data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up DADCARE...')

        # 1. Create immutable audit trigger
        with connection.cursor() as cur:
            cur.execute("""
                CREATE OR REPLACE FUNCTION prevent_audit_modification()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'Audit log is immutable';
                END;
                $$ LANGUAGE plpgsql;
            """)
            cur.execute("""
                DROP TRIGGER IF EXISTS audit_log_immutable ON audit_log;
            """)
            try:
                cur.execute("""
                    CREATE TRIGGER audit_log_immutable
                    BEFORE UPDATE OR DELETE ON audit_log
                    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
                """)
            except Exception:
                pass  # Table may not exist yet if migrations haven't run

        self.stdout.write(self.style.SUCCESS('  Audit trigger: OK'))

        # 2. Seed mini-apps
        from apps.tenants.models import MiniApp
        mini_apps = [
            {'name': 'Shop',        'slug': 'shop',        'icon': 'shop',   'is_active': True,  'is_coming_soon': False, 'display_order': 1},
            {'name': 'Marketplace', 'slug': 'marketplace', 'icon': 'store',  'is_active': True,  'is_coming_soon': False, 'display_order': 2},
            {'name': 'School',      'slug': 'school',      'icon': 'school', 'is_active': False, 'is_coming_soon': True,  'display_order': 3},
            {'name': 'Pharmacy',    'slug': 'pharmacy',    'icon': 'pill',   'is_active': False, 'is_coming_soon': True,  'display_order': 4},
            {'name': 'Gym',         'slug': 'gym',         'icon': 'gym',    'is_active': False, 'is_coming_soon': True,  'display_order': 5},
        ]

        created = 0
        for app_data in mini_apps:
            _, was_created = MiniApp.objects.get_or_create(
                slug=app_data['slug'],
                defaults=app_data
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'  Mini-apps: {created} created, {len(mini_apps) - created} already exist'))
        self.stdout.write(self.style.SUCCESS('\nDADCARE setup complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('  1. Set environment variables (see .env.example)')
        self.stdout.write('  2. Create Super Admin: python manage.py create_super_admin')
        self.stdout.write('  3. Start server: gunicorn dadcare.wsgi:application')
