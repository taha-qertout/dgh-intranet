from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Department

PASSWORD = "Str0ngPass!23"


class AuthTests(TestCase):
    """Login/logout behaviour, and the RoleRequiredMixin anonymous-access
    regression (see accounts/mixins.py)."""

    def setUp(self):
        self.rh = Department.objects.create(code="RH", name="Ressources Humaines")

        User = get_user_model()
        self.chef = User.objects.create_user(
            username="chef_test",
            password=PASSWORD,
            role="chef",
            department=self.rh,
        )

    def test_login_success_redirects_to_documents(self):
        response = self.client.post(
            reverse("login"), {"username": "chef_test", "password": PASSWORD}
        )
        self.assertRedirects(response, "/documents/")

    def test_login_failure_wrong_password_shows_form_error_no_redirect(self):
        response = self.client.post(
            reverse("login"), {"username": "chef_test", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_post_redirects_to_login(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_logout_get_returns_405(self):
        self.client.login(username="chef_test", password=PASSWORD)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_anonymous_hitting_role_required_view_redirects_to_login_not_500(self):
        url = reverse("documents:document_upload")
        response = self.client.get(url)
        expected_url = f"{reverse('login')}?next={url}"
        self.assertRedirects(response, expected_url)
