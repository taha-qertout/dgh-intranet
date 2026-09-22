from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from audit.models import AuditLog
from core.models import Announcement, Department

PASSWORD = "Str0ngPass!23"


class AnnouncementsTestBase(TestCase):
    """Department + role-user setup, mirroring DocumentsTestBase in
    documents/tests.py. No MEDIA_ROOT override here (unlike
    TempMediaTestCase in that file) — Announcement has no file field, so
    no test ever writes to storage.

    Unlike Document, department scoping needs to be exercised from both
    sides (RH and INFO), so this adds a second chef in INFO alongside the
    RH admin/chef/employe trio.
    """

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
        self.info_chef = User.objects.create_user(
            username="info_chef_test",
            password=PASSWORD,
            role="chef",
            department=self.info,
        )


class VisibleToQuerySetTests(AnnouncementsTestBase):
    def setUp(self):
        super().setUp()
        self.rh_announcement = Announcement.objects.create(
            title="Annonce RH",
            body="Contenu RH",
            department=self.rh,
            posted_by=self.chef,
        )
        self.info_announcement = Announcement.objects.create(
            title="Annonce INFO",
            body="Contenu INFO",
            department=self.info,
            posted_by=self.info_chef,
        )
        self.org_wide_announcement = Announcement.objects.create(
            title="Annonce generale",
            body="Contenu general",
            department=None,
            posted_by=self.admin,
        )
        self.inactive_org_wide_announcement = Announcement.objects.create(
            title="Ancienne annonce generale",
            body="Contenu obsolete",
            department=None,
            posted_by=self.admin,
            is_active=False,
        )

    def test_admin_sees_all_active_announcements(self):
        visible = Announcement.objects.visible_to(self.admin)
        self.assertCountEqual(
            visible,
            [self.rh_announcement, self.info_announcement, self.org_wide_announcement],
        )

    def test_rh_chef_sees_own_department_and_org_wide_not_info(self):
        visible = Announcement.objects.visible_to(self.chef)
        self.assertCountEqual(visible, [self.rh_announcement, self.org_wide_announcement])

    def test_rh_employe_sees_same_set_as_rh_chef(self):
        visible = Announcement.objects.visible_to(self.employe)
        self.assertCountEqual(visible, [self.rh_announcement, self.org_wide_announcement])

    def test_info_user_sees_own_department_and_org_wide_not_rh(self):
        visible = Announcement.objects.visible_to(self.info_chef)
        self.assertCountEqual(visible, [self.info_announcement, self.org_wide_announcement])

    def test_soft_deleted_excluded_for_every_role_including_org_wide(self):
        for user in (self.admin, self.chef, self.employe, self.info_chef):
            visible = Announcement.objects.visible_to(user)
            self.assertNotIn(self.inactive_org_wide_announcement, visible)

    def test_admin_with_no_department_sees_everything_not_just_org_wide(self):
        # admin.department is None, same shape as a "no department"
        # non-admin — the admin branch must short-circuit before the
        # department check, or this would silently degrade to org-wide-only.
        self.assertIsNone(self.admin.department_id)
        visible = Announcement.objects.visible_to(self.admin)
        self.assertIn(self.rh_announcement, visible)
        self.assertIn(self.info_announcement, visible)
        self.assertIn(self.org_wide_announcement, visible)


class ViewEnforcementTests(AnnouncementsTestBase):
    """Proves the views actually call visible_to(), not just that the
    queryset method works in isolation."""

    def setUp(self):
        super().setUp()
        self.rh_announcement = Announcement.objects.create(
            title="Annonce RH",
            body="Contenu RH",
            department=self.rh,
            posted_by=self.chef,
        )
        self.info_announcement = Announcement.objects.create(
            title="Annonce INFO",
            body="Contenu INFO",
            department=self.info,
            posted_by=self.info_chef,
        )
        self.org_wide_announcement = Announcement.objects.create(
            title="Annonce generale",
            body="Contenu general",
            department=None,
            posted_by=self.admin,
        )

    def test_detail_view_cross_department_announcement_is_404(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_detail", args=[self.info_announcement.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_org_wide_announcement_reachable_by_anyone(self):
        # A naive department-equality check (announcement.department ==
        # user.department) would wrongly 404 here, since department is
        # None on both sides for unrelated reasons.
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_detail", args=[self.org_wide_announcement.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_anonymous_redirected_to_login(self):
        url = reverse("announcements:announcement_list")
        response = self.client.get(url)
        expected_url = f"{reverse('login')}?next={url}"
        self.assertRedirects(response, expected_url)


class CreateTests(AnnouncementsTestBase):
    def test_employe_gets_403(self):
        self.client.login(username="employe_test", password=PASSWORD)
        response = self.client.get(reverse("announcements:announcement_create"))
        self.assertEqual(response.status_code, 403)

    def test_chef_can_access_and_post_ignoring_submitted_department(self):
        self.client.login(username="chef_test", password=PASSWORD)

        get_response = self.client.get(reverse("announcements:announcement_create"))
        self.assertEqual(get_response.status_code, 200)

        response = self.client.post(
            reverse("announcements:announcement_create"),
            {
                "title": "Nouvelle annonce",
                "body": "Contenu de l'annonce.",
                # "department" is not a form field at all; posting one must
                # be silently ignored, not accepted.
                "department": self.info.pk,
            },
        )
        self.assertRedirects(response, reverse("announcements:announcement_list"))
        announcement = Announcement.objects.get(title="Nouvelle annonce")
        self.assertEqual(announcement.posted_by_id, self.chef.pk)
        self.assertEqual(announcement.department_id, self.rh.pk)

    def test_admin_post_creates_org_wide_announcement(self):
        self.client.login(username="admin_test", password=PASSWORD)
        response = self.client.post(
            reverse("announcements:announcement_create"),
            {
                "title": "Annonce direction",
                "body": "Contenu direction.",
            },
        )
        self.assertRedirects(response, reverse("announcements:announcement_list"))
        announcement = Announcement.objects.get(title="Annonce direction")
        self.assertEqual(announcement.posted_by_id, self.admin.pk)
        self.assertIsNone(announcement.department_id)


class SoftDeleteTests(AnnouncementsTestBase):
    def setUp(self):
        super().setUp()
        self.rh_announcement = Announcement.objects.create(
            title="Annonce RH",
            body="Contenu RH",
            department=self.rh,
            posted_by=self.chef,
        )
        self.info_announcement = Announcement.objects.create(
            title="Annonce INFO",
            body="Contenu INFO",
            department=self.info,
            posted_by=self.info_chef,
        )

    def test_get_delete_url_renders_confirmation_without_deleting(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_delete", args=[self.rh_announcement.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/announcement_confirm_delete.html")
        self.rh_announcement.refresh_from_db()
        self.assertTrue(self.rh_announcement.is_active)

    def test_chef_deletes_own_active_departmental_announcement(self):
        self.assertEqual(self.rh_announcement.posted_by_id, self.chef.pk)
        self.assertEqual(self.rh_announcement.department_id, self.rh.pk)
        self.assertTrue(self.rh_announcement.is_active)
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_delete", args=[self.rh_announcement.pk]
        )
        response = self.client.post(url)
        self.assertRedirects(response, reverse("announcements:announcement_list"))
        self.rh_announcement.refresh_from_db()
        self.assertFalse(self.rh_announcement.is_active)
        # Unfiltered default manager: proves this is a soft delete, not a
        # real row removal.
        self.assertTrue(
            Announcement.objects.filter(pk=self.rh_announcement.pk).exists()
        )

    def test_chef_cannot_delete_another_authors_departmental_announcement(self):
        other_chef = get_user_model().objects.create_user(
            username="other_rh_chef",
            password=PASSWORD,
            role="chef",
            department=self.rh,
        )
        announcement = Announcement.objects.create(
            title="Annonce autre Chef RH",
            body="Contenu RH",
            department=self.rh,
            posted_by=other_chef,
        )
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("announcements:announcement_delete", args=[announcement.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        announcement.refresh_from_db()
        self.assertTrue(announcement.is_active)

    def test_chef_cannot_delete_org_wide_admin_announcement(self):
        announcement = Announcement.objects.create(
            title="Annonce direction",
            body="Contenu général",
            department=None,
            posted_by=self.admin,
        )
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse("announcements:announcement_delete", args=[announcement.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        announcement.refresh_from_db()
        self.assertTrue(announcement.is_active)

    def test_admin_can_soft_delete_any_visible_announcement(self):
        org_wide = Announcement.objects.create(
            title="Annonce direction",
            body="Contenu général",
            department=None,
            posted_by=self.admin,
        )
        self.client.login(username="admin_test", password=PASSWORD)
        for announcement in (self.rh_announcement, self.info_announcement, org_wide):
            url = reverse("announcements:announcement_delete", args=[announcement.pk])
            self.assertRedirects(
                self.client.post(url), reverse("announcements:announcement_list")
            )
            announcement.refresh_from_db()
            self.assertFalse(announcement.is_active)
            self.assertTrue(Announcement.objects.filter(pk=announcement.pk).exists())

    def test_inactive_own_announcement_cannot_be_deleted_again(self):
        self.rh_announcement.is_active = False
        self.rh_announcement.save()
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_delete", args=[self.rh_announcement.pk]
        )
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_detail_only_offers_delete_to_authorized_user(self):
        org_wide = Announcement.objects.create(
            title="Annonce direction",
            body="Contenu général",
            department=None,
            posted_by=self.admin,
        )
        other_chef = get_user_model().objects.create_user(
            username="other_rh_chef",
            password=PASSWORD,
            role="chef",
            department=self.rh,
        )
        other_post = Announcement.objects.create(
            title="Annonce autre Chef RH",
            body="Contenu RH",
            department=self.rh,
            posted_by=other_chef,
        )
        self.client.login(username="chef_test", password=PASSWORD)
        for announcement, should_offer_delete in (
            (self.rh_announcement, True),
            (other_post, False),
            (org_wide, False),
        ):
            detail_url = reverse("announcements:announcement_detail", args=[announcement.pk])
            delete_url = reverse("announcements:announcement_delete", args=[announcement.pk])
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 200)
            if should_offer_delete:
                self.assertContains(response, delete_url)
            else:
                self.assertNotContains(response, delete_url)

    def test_django_admin_cannot_hard_delete_announcement(self):
        request = RequestFactory().get("/admin/core/announcement/")
        request.user = self.admin
        model_admin = admin.site._registry[Announcement]
        self.assertFalse(model_admin.has_delete_permission(request))

        self.client.login(username="admin_test", password=PASSWORD)
        url = reverse("admin:core_announcement_delete", args=[self.rh_announcement.pk])
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        self.assertTrue(Announcement.objects.filter(pk=self.rh_announcement.pk).exists())

    def test_chef_deleting_other_department_announcement_is_404(self):
        self.client.login(username="chef_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_delete", args=[self.info_announcement.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_employe_gets_403_on_delete_url(self):
        self.client.login(username="employe_test", password=PASSWORD)
        url = reverse(
            "announcements:announcement_delete", args=[self.rh_announcement.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class AuditLoggingTests(AnnouncementsTestBase):
    """Announcements are the first feature exercising log_action's
    announcement= branch — documents/tests.py never asserted on AuditLog
    rows at all."""

    def test_chef_create_logs_entry_with_chefs_department(self):
        self.client.login(username="chef_test", password=PASSWORD)
        self.client.post(
            reverse("announcements:announcement_create"),
            {"title": "Annonce auditee", "body": "Contenu."},
        )
        entry = AuditLog.objects.get(action=AuditLog.Action.ANNOUNCEMENT_CREATE)
        self.assertEqual(entry.username, "chef_test")
        self.assertEqual(entry.department_id, self.rh.pk)

    def test_admin_create_logs_entry_with_no_department(self):
        # department=None here must come from the announcement's own
        # (org-wide) department, not be silently backfilled from anywhere
        # else — the admin has no department to fall back to either.
        self.client.login(username="admin_test", password=PASSWORD)
        self.client.post(
            reverse("announcements:announcement_create"),
            {"title": "Annonce direction auditee", "body": "Contenu."},
        )
        entry = AuditLog.objects.get(action=AuditLog.Action.ANNOUNCEMENT_CREATE)
        self.assertEqual(entry.username, "admin_test")
        self.assertIsNone(entry.department_id)

    def test_delete_logs_entry_with_announcement_title(self):
        self.client.login(username="chef_test", password=PASSWORD)
        announcement = Announcement.objects.create(
            title="Annonce a supprimer",
            body="Contenu.",
            department=self.rh,
            posted_by=self.chef,
        )
        self.client.post(
            reverse("announcements:announcement_delete", args=[announcement.pk])
        )
        entry = AuditLog.objects.get(action=AuditLog.Action.ANNOUNCEMENT_DELETE)
        self.assertEqual(entry.document_title, "Annonce a supprimer")
