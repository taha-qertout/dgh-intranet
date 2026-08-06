from django.conf import settings
from django.db import models


class DocumentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def visible_to(self, user):
        qs = self.active()
        if user.role == "admin":
            return qs
        if user.department_id is None:
            return qs.none()
        return qs.filter(department_id=user.department_id)


class Document(models.Model):
    class Category(models.TextChoices):
        NOTE_SERVICE = "note_service", "Note de service"
        RAPPORT = "rapport", "Rapport"
        FORMULAIRE = "formulaire", "Formulaire"
        PROCEDURE = "procedure", "Procédure"
        AUTRE = "autre", "Autre"

    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    file = models.FileField(
        upload_to="documents/%Y/%m/", verbose_name="Fichier"
    )
    department = models.ForeignKey(
        "core.Department",
        on_delete=models.PROTECT,
        related_name="documents",
        null=False,
        blank=False,
        verbose_name="Département",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_documents",
        verbose_name="Ajouté par",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        verbose_name="Catégorie",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date d'ajout"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    objects = DocumentQuerySet.as_manager()

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
