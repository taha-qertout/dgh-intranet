from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model, kept as a plain AbstractUser subclass for now.

    Introduced before the first migration specifically so this app can gain
    fields (role, department, ...) later without the "swap the user model
    after migrate" problem. Do not add fields here without a design pass —
    see docs/permission-matrix.md.
    """

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
