import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Department
from documents.models import Document

PASSWORD = "Str0ngPass!23"


def make_uploaded_file(name="doc.pdf", content=b"%PDF-1.4 sample content", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


class TempMediaTestCase(TestCase):
    """Every subclass gets its own throwaway MEDIA_ROOT so test runs never
    write into the real media/ folder used for manual testing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media_dir = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media_dir)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._temp_media_dir, ignore_errors=True)
        super().tearDownClass()


class DocumentsTestBase(TempMediaTestCase):
    """Department + three-role-user setup, mirroring seed_demo_data."""

    def setUp(self):
        self.rh = Department.objects.create(code="RH", name="Ressources Humaines")
        self.info = Department.objects.create(code="INFO", name="Informatique")

        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin_test",
            password=PASSWORD,
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
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


class VisibleToQuerySetTests(DocumentsTestBase):
    def setUp(self):
        super().setUp()
        self.rh_doc = Document.objects.create(
            title="Note de service RH",
            file=make_uploaded_file("rh.pdf"),
            department=self.rh,
            uploaded_by=self.chef,
            category=Document.Category.NOTE_SERVICE,
        )
        self.info_doc = Document.objects.create(
            title="Rapport INFO",
            file=make_uploaded_file("info.pdf"),
            department=self.info,
            uploaded_by=self.admin,
            category=Document.Category.RAPPORT,
        )
        self.inactive_rh_doc = Document.objects.create(
            title="Ancien document RH",
            file=make_uploaded_file("old.pdf"),
            department=self.rh,
            uploaded_by=self.chef,
            category=Document.Category.AUTRE,
            is_active=False,
        )

    def test_admin_sees_all_active_documents_across_departments(self):
        visible = Document.objects.visible_to(self.admin)
        self.assertCountEqual(visible, [self.rh_doc, self.info_doc])

    def test_chef_sees_only_own_department_documents(self):
        visible = Document.objects.visible_to(self.chef)
        self.assertCountEqual(visible, [self.rh_doc])

    def test_employe_sees_only_own_department_documents(self):
        visible = Document.objects.visible_to(self.employe)
        self.assertCountEqual(visible, [self.rh_doc])

    def test_soft_deleted_excluded_for_every_role(self):
        for user in (self.admin, self.chef, self.employe):
            visible = Document.objects.visible_to(user)
            self.assertNotIn(self.inactive_rh_doc, visible)

    def test_non_admin_with_no_department_returns_empty_queryset(self):
        User = get_user_model()
        orphan = User.objects.create_user(
            username="orphan_test",
            password=PASSWORD,
            role="employe",
            department=None,
        )
        visible = Document.objects.visible_to(orphan)
        self.assertQuerySetEqual(visible, [])


class ViewEnforcementTests(DocumentsTestBase):
    """Proves the views actually call visible_to(), not just that the
    queryset method works in isolation."""

    def setUp(self):
        super().setUp()
        self.rh_doc = Document.objects.create(
            title="Note RH",
            file=make_uploaded_file("rh.pdf"),
            department=self.rh,
            uploaded_by=self.chef,
            category=Document.Category.NOTE_SERVICE,
        )
        self.info_doc = Document.objects.create(
            title="Rapport INFO",
            file=make_uploaded_file("info.pdf"),
            department=self.info,
            uploaded_by=self.admin,
            category=Document.Category.RAPPORT,
        )

    def test_detail_view_cross_department_document_is_404(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_detail", args=[self.info_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_download_cross_department_document_is_404(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_download", args=[self.info_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_download_in_scope_document_returns_file_response(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_download", args=[self.rh_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, FileResponse)
        self.assertTrue(response["Content-Disposition"].startswith("attachment"))


class UploadTests(DocumentsTestBase):
    def test_employe_gets_403(self):
        self.client.login(username="employe_test", password=PASSWORD)
        response = self.client.get(reverse("documents:document_upload"))
        self.assertEqual(response.status_code, 403)

    def test_chef_can_access_and_successfully_post(self):
        self.client.login(username="chef_test", password=PASSWORD)

        get_response = self.client.get(reverse("documents:document_upload"))
        self.assertEqual(get_response.status_code, 200)

        response = self.client.post(
            reverse("documents:document_upload"),
            {
                "title": "Nouveau document",
                "description": "Une description.",
                "file": make_uploaded_file("nouveau.pdf"),
                "category": Document.Category.RAPPORT,
            },
        )
        self.assertRedirects(response, reverse("documents:document_list"))
        self.assertEqual(Document.objects.count(), 1)

    def test_upload_ignores_submitted_department_uses_chefs_own(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.post(
            reverse("documents:document_upload"),
            {
                "title": "Doc departement usurpe",
                "description": "",
                "file": make_uploaded_file("usurpe.pdf"),
                "category": Document.Category.AUTRE,
                # "department" is not a form field at all; posting one must
                # be silently ignored, not accepted.
                "department": self.info.pk,
            },
        )
        self.assertRedirects(response, reverse("documents:document_list"))
        document = Document.objects.get(title="Doc departement usurpe")
        self.assertEqual(document.department_id, self.rh.pk)
        self.assertEqual(document.uploaded_by_id, self.chef.pk)

    def test_upload_file_over_10mb_rejected_with_french_message(self):
        self.client.login(username="chef_test", password=PASSWORD)
        big_content = b"x" * (10 * 1024 * 1024 + 1)
        response = self.client.post(
            reverse("documents:document_upload"),
            {
                "title": "Trop gros",
                "description": "",
                "file": SimpleUploadedFile(
                    "gros.pdf", big_content, content_type="application/pdf"
                ),
                "category": Document.Category.AUTRE,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "file",
            "Le fichier ne doit pas dépasser 10 Mo.",
        )
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_disallowed_extension_rejected_with_french_message(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.post(
            reverse("documents:document_upload"),
            {
                "title": "Extension refusee",
                "description": "",
                "file": SimpleUploadedFile(
                    "notes.txt", b"plain text", content_type="text/plain"
                ),
                "category": Document.Category.AUTRE,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "file",
            "Type de fichier non autorisé. Formats acceptés : PDF, Word, Excel, images.",
        )
        self.assertEqual(Document.objects.count(), 0)


class SoftDeleteTests(DocumentsTestBase):
    def setUp(self):
        super().setUp()
        self.rh_doc = Document.objects.create(
            title="Note RH",
            file=make_uploaded_file("rh.pdf"),
            department=self.rh,
            uploaded_by=self.chef,
            category=Document.Category.NOTE_SERVICE,
        )
        self.info_doc = Document.objects.create(
            title="Rapport INFO",
            file=make_uploaded_file("info.pdf"),
            department=self.info,
            uploaded_by=self.admin,
            category=Document.Category.RAPPORT,
        )

    def test_get_delete_url_renders_confirmation_without_deleting(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_delete", args=[self.rh_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "documents/document_confirm_delete.html")
        self.rh_doc.refresh_from_db()
        self.assertTrue(self.rh_doc.is_active)

    def test_post_delete_soft_deletes_row_stays_in_db(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_delete", args=[self.rh_doc.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("documents:document_list"))
        self.rh_doc.refresh_from_db()
        self.assertFalse(self.rh_doc.is_active)
        # Unfiltered default manager: proves this is a soft delete, not a
        # real row removal.
        self.assertTrue(Document.objects.filter(pk=self.rh_doc.pk).exists())

    def test_chef_deleting_other_department_document_is_404(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("documents:document_delete", args=[self.info_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_employe_cannot_reach_delete_url(self):
        self.client.login(username="employe_test", password=PASSWORD)
        url = reverse("documents:document_delete", args=[self.rh_doc.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
