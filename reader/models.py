from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=240)
    pdf = models.FileField(upload_to="documents/%Y/%m/", validators=[FileExtensionValidator(["pdf"])])
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_page = models.PositiveIntegerField(default=1)
    last_zoom = models.FloatField(default=1.0)
    class Meta:
        ordering = ["-uploaded_at"]
    def __str__(self):
        return self.title

class Note(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reader_notes")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="notes")
    text = models.TextField()
    page = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]

class Bookmark(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reader_bookmarks")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="bookmarks")
    page = models.PositiveIntegerField(default=1)
    label = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["page", "created_at"]
        constraints = [models.UniqueConstraint(fields=["owner", "document", "page"], name="unique_user_doc_bookmark_page")]

class Highlight(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reader_highlights")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="highlights")
    text = models.TextField()
    page = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=20, default="yellow")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]

class ReadingProgress(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_progress")
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name="progress")
    page = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
