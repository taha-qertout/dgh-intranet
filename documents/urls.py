from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="document_list"),
    path("<int:pk>/", views.DocumentDetailView.as_view(), name="document_detail"),
    path(
        "<int:pk>/telecharger/",
        views.document_download,
        name="document_download",
    ),
    path("ajouter/", views.DocumentUploadView.as_view(), name="document_upload"),
    path(
        "<int:pk>/supprimer/",
        views.DocumentDeleteView.as_view(),
        name="document_delete",
    ),
]
