from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Connexion réussie"
        LOGIN_FAILED = "login_failed", "Échec de connexion"
        LOGOUT = "logout", "Déconnexion"
        DOCUMENT_UPLOAD = "document_upload", "Ajout d'un document"
        DOCUMENT_DOWNLOAD = "document_download", "Téléchargement d'un document"
        DOCUMENT_DELETE = "document_delete", "Suppression d'un document"
        ANNOUNCEMENT_CREATE = "announcement_create", "Publication d'une annonce"
        ANNOUNCEMENT_DELETE = "announcement_delete", "Suppression d'une annonce"

    action = models.CharField(
        max_length=30, choices=Action.choices, verbose_name="Action"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        verbose_name="Utilisateur",
    )
    username = models.CharField(
        max_length=150, blank=True, verbose_name="Nom d'utilisateur"
    )
    department = models.ForeignKey(
        "core.Department",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_entries",
        verbose_name="Département",
    )
    document = models.ForeignKey(
        "documents.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        verbose_name="Document",
    )
    document_title = models.CharField(
        max_length=200, blank=True, verbose_name="Titre du document"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Adresse IP"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Date et heure"
    )

    class Meta:
        verbose_name = "Entrée du journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} – {self.username} – {self.get_action_display()}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Les entrées du journal d'audit sont immuables.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Les entrées du journal d'audit ne peuvent pas être supprimées."
        )
