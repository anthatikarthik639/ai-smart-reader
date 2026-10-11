from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("library/", views.library, name="library"),
    path("upload/", views.upload_document, name="upload_document"),
    path("reader/<int:document_id>/", views.read_document, name="read_document"),
    path("document/<int:document_id>/delete/", views.delete_document, name="delete_document"),
    path("api/ai/", views.ai_api, name="ai_api"),
    path("api/notes/", views.notes_api, name="notes_api"),
    path("api/notes/<int:note_id>/", views.note_detail_api, name="note_detail_api"),
    path("api/bookmarks/", views.bookmarks_api, name="bookmarks_api"),
    path("api/bookmarks/<int:bookmark_id>/", views.bookmark_detail_api, name="bookmark_detail_api"),
    path("api/highlights/", views.highlights_api, name="highlights_api"),
    path("api/highlights/<int:highlight_id>/", views.highlight_detail_api, name="highlight_detail_api"),
    path("api/progress/", views.progress_api, name="progress_api"),
]
