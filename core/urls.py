from django.urls import path

from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.AnnouncementListView.as_view(), name="announcement_list"),
    path(
        "<int:pk>/",
        views.AnnouncementDetailView.as_view(),
        name="announcement_detail",
    ),
    path(
        "ajouter/",
        views.AnnouncementCreateView.as_view(),
        name="announcement_create",
    ),
    path(
        "<int:pk>/supprimer/",
        views.AnnouncementDeleteView.as_view(),
        name="announcement_delete",
    ),
]
