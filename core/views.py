from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import RoleRequiredMixin
from audit.models import AuditLog
from audit.services import log_action

from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementListView(LoginRequiredMixin, ListView):
    template_name = "core/announcement_list.html"
    context_object_name = "announcements"
    paginate_by = 20

    def get_queryset(self):
        return Announcement.objects.visible_to(self.request.user)


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    template_name = "core/announcement_detail.html"
    context_object_name = "announcement"

    def get_queryset(self):
        return Announcement.objects.visible_to(self.request.user)


class AnnouncementCreateView(RoleRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "core/announcement_form.html"
    allowed_roles = ["chef", "admin"]
    success_url = reverse_lazy("announcements:announcement_list")

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        form.instance.department = self.request.user.department
        response = super().form_valid(form)
        log_action(
            AuditLog.Action.ANNOUNCEMENT_CREATE,
            user=self.request.user,
            announcement=self.object,
            request=self.request,
        )
        return response


class AnnouncementDeleteView(RoleRequiredMixin, DetailView):
    template_name = "core/announcement_confirm_delete.html"
    context_object_name = "announcement"
    allowed_roles = ["chef", "admin"]

    def get_queryset(self):
        return Announcement.objects.visible_to(self.request.user)

    def post(self, request, *args, **kwargs):
        announcement = self.get_object()
        announcement.is_active = False
        announcement.save()
        log_action(
            AuditLog.Action.ANNOUNCEMENT_DELETE,
            user=request.user,
            announcement=announcement,
            request=request,
        )
        return redirect("announcements:announcement_list")
