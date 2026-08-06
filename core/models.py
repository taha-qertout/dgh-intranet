from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"

    def __str__(self):
        return self.name


class AnnouncementQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def visible_to(self, user):
        qs = self.active()
        if user.role == "admin":
            return qs
        if user.department_id is None:
            return qs.filter(department__isnull=True)
        return qs.filter(
            models.Q(department_id=user.department_id) | models.Q(department__isnull=True)
        )


class Announcement(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    body = models.TextField(verbose_name="Contenu")
    department = models.ForeignKey(
        "core.Department",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="announcements",
        verbose_name="Département",
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="announcements",
        verbose_name="Publié par",
    )
    published_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de publication"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    objects = AnnouncementQuerySet.as_manager()

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title
