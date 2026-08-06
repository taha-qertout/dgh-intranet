from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model, introduced before the first migration specifically
    so this app can gain fields without the "swap the user model after
    migrate" problem. Field additions follow the design in
    docs/permission-matrix.md.
    """

    department = models.ForeignKey(
        "core.Department",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
        verbose_name="Département",
    )
    role = models.CharField(
        max_length=10,
        choices=[
            ("admin", "Admin"),
            ("chef", "Chef de Département"),
            ("employe", "Employé"),
        ],
        verbose_name="Rôle",
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
