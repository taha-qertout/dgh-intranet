from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import Department

from .models import AuditLog

PASSWORD = "Str0ngPass!23"


class AuditLogImmutabilityTests(TestCase):
    """Codifies the manual shell verification of AuditLog.save()/delete()
    guards (see audit/models.py)."""

    def setUp(self):
        self.entry = AuditLog.objects.create(
            action=AuditLog.Action.LOGIN_SUCCESS,
            username="chef_test",
        )

    def test_save_on_existing_entry_raises_validation_error(self):
        self.entry.ip_address = "127.0.0.1"
        with self.assertRaises(ValidationError):
            self.entry.save()

    def test_delete_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.entry.delete()

    def test_entry_still_exists_after_blocked_mutations(self):
        self.entry.ip_address = "127.0.0.1"
        try:
            self.entry.save()
        except ValidationError:
            pass
        try:
            self.entry.delete()
        except ValidationError:
            pass
        self.assertTrue(AuditLog.objects.filter(pk=self.entry.pk).exists())


class AuditLogListViewTests(TestCase):
    def setUp(self):
        self.rh = Department.objects.create(code="RH", name="Ressources Humaines")
        self.info = Department.objects.create(code="INFO", name="Informatique")

        User = get_user_model()
        self.chef = User.objects.create_user(
            username="chef_test",
            password=PASSWORD,
            role="chef",
            department=self.rh,
        )
        self.employe = User.objects.create_user(
            username="employe_test",
            password=PASSWORD,
            role="employe",
            department=self.rh,
        )

        self.rh_entry = AuditLog.objects.create(
            action=AuditLog.Action.DOCUMENT_UPLOAD,
            username="chef_test",
            department=self.rh,
            document_title="Note RH",
        )
        self.info_entry = AuditLog.objects.create(
            action=AuditLog.Action.DOCUMENT_UPLOAD,
            username="autre_chef",
            department=self.info,
            document_title="Rapport INFO",
        )

    def test_chef_sees_only_own_department_entries(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.get(reverse("audit:auditlog_list"))
        self.assertEqual(response.status_code, 200)
        entries = response.context["audit_entries"]
        # The login itself writes its own audit entry (department=RH, via
        # the resolved-user fallback in log_action), so this asserts scope
        # rather than an exact count: the seeded RH entry is present, and
        # every visible entry belongs to the chef's own department.
        self.assertIn(self.rh_entry, entries)
        for entry in entries:
            self.assertEqual(entry.department_id, self.rh.pk)

    def test_other_department_entries_excluded(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.get(reverse("audit:auditlog_list"))
        self.assertNotIn(self.info_entry, response.context["audit_entries"])

    def test_employe_gets_403(self):
        self.client.login(username="employe_test", password=PASSWORD)
        response = self.client.get(reverse("audit:auditlog_list"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        url = reverse("audit:auditlog_list")
        response = self.client.get(url)
        expected_url = f"{reverse('login')}?next={url}"
        self.assertRedirects(response, expected_url)
