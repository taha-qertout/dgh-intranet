import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import RoleRequiredMixin

from .forms import DocumentUploadForm
from .models import Document


class DocumentListView(LoginRequiredMixin, ListView):
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self):
        return Document.objects.visible_to(self.request.user)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    template_name = "documents/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.visible_to(self.request.user)


@login_required
def document_download(request, pk):
    document = get_object_or_404(
        Document.objects.visible_to(request.user), pk=pk
    )
    filename = os.path.basename(document.file.name)
    return FileResponse(
        document.file.open("rb"), as_attachment=True, filename=filename
    )


class DocumentUploadView(RoleRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = "documents/document_upload.html"
    allowed_roles = ["chef"]
    success_url = reverse_lazy("documents:document_list")

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.department = self.request.user.department
        return super().form_valid(form)


class DocumentDeleteView(RoleRequiredMixin, DetailView):
    template_name = "documents/document_confirm_delete.html"
    context_object_name = "document"
    allowed_roles = ["chef", "admin"]

    def get_queryset(self):
        return Document.objects.visible_to(self.request.user)

    def post(self, request, *args, **kwargs):
        document = self.get_object()
        document.is_active = False
        document.save()
        return redirect("documents:document_list")
