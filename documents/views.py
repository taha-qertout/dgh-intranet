import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

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
