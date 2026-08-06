from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Department

DEMO_PASSWORD = "DemoPass123!"


class Command(BaseCommand):
    help = "Seed local dev demo data: departments and demo users. Idempotent."

    def handle(self, *args, **options):
        User = get_user_model()

        departments = {}
        dept_created = 0
        dept_existing = 0
        for code, name in [("RH", "Ressources Humaines"), ("INFO", "Informatique")]:
            dept, created = Department.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            departments[code] = dept
            if created:
                dept_created += 1
                self.stdout.write(f"Département créé : {dept.name} ({dept.code})")
            else:
                dept_existing += 1
                self.stdout.write(
                    f"Département déjà existant : {dept.name} ({dept.code})"
                )

        users_spec = [
            {
                "username": "admin_demo",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
                "department": None,
            },
            {
                "username": "chef_demo",
                "role": "chef",
                "is_staff": False,
                "is_superuser": False,
                "department": departments["RH"],
            },
            {
                "username": "employe_demo",
                "role": "employe",
                "is_staff": False,
                "is_superuser": False,
                "department": departments["RH"],
            },
        ]

        user_created = 0
        user_existing = 0
        for spec in users_spec:
            username = spec["username"]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": spec["role"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                    "department": spec["department"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                user_created += 1
                self.stdout.write(f"Utilisateur créé : {username} (role={user.role})")
            else:
                user_existing += 1
                self.stdout.write(f"Utilisateur déjà existant : {username}")

        self.stdout.write(self.style.SUCCESS("\nRésumé :"))
        self.stdout.write(
            f"  Départements : {dept_created} créé(s), {dept_existing} déjà existant(s)"
        )
        self.stdout.write(
            f"  Utilisateurs : {user_created} créé(s), {user_existing} déjà existant(s)"
        )
